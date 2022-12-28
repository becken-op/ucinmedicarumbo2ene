import base64
import logging
import time
import babel
from datetime import datetime, timedelta, time
from os import path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pytz import timezone
from lxml import etree, objectify
from suds.client import Client
from odoo.addons.l10n_mx_edi.models import account_invoice
from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from .safe_eval import ast, Transformer
from .jinja_extension import RaiseExtension
from itertools import groupby
from odoo.addons.l10n_mx_edi.tools.run_after_commit import run_after_commit
from lxml.objectify import fromstring
from odoo.tools.float_utils import float_repr
import requests
import tempfile

CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
} 
CFDI_XSLT_CADENA = 'hr_payroll_mxn/SAT/cadenaoriginal_3_3.xslt' 

_logger = logging.getLogger(__name__)

_errors = {
    'bank_account': _('Missing bank account for employee.'),
    'employer_number': _('Missing employer number.'),
    'social_security': _('Missing social security number for employee.'),
    'payslip_type': _('Missing payslip type on payroll structure.'),
    'contract_type': _('Missing code for contract type.'),
    'company_curp': _('CURP is required when company is a Person.'),
    'tipo_regimen_tipo_contrato': _(
        'When Contract Type code is between 01 and 08, '
        'then Employee Regime must be 02, 03 or 04.',
    ),
}


def create_list_html(array):
    '''Convert an array of string to a html list.
    :param array: A list of strings
    :return: an empty string if not array, an html list otherwise.
    '''
    if not array:
        return ''
    msg = ''
    for item in array:
        msg += '<li>' + item + '</li>'
    return '<ul>' + msg + '</ul>'


def _domain2statement(domain):
    statement = ''
    operator = False
    for d in domain:
        if not operator:
            if isinstance(d, str):
                if d == '|':
                    operator = ' or'
                continue
            else:
                operator = False
        statement += ' o.' + str(d[0]) + ' '
        statement += (d[1] == '=' and '==' or d[1]) + ' '
        statement += (
            (isinstance(d[2], str) and '\'' + d[2] + '\'' or str(d[2]))
        )
        if d != domain[-1]:
            statement += operator or ' and'
        operator = False


def required_field(value, error):
    """Filter used to enforce a required value on template

    @param value: Value to evaluate and enforce presence
    @type value: any
    @param error: Error message to display if value not present
    @type error: str
    @raise ValidationError: if value is not set
    """
    if not value:
        raise ValidationError(error)
    return value


class InheritAccountInvoice(models.Model):
    _inherit = 'account.move'

    @classmethod
    def generate_cadena_original(self, xml, context=None):
        xlst_file = tools.file_open(context.get('path_cadena', '')).name
        dom = etree.fromstring(xml)
        xslt = etree.parse(xlst_file)
        transform = etree.XSLT(xslt)
        return str(transform(dom))


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread']

    @api.model
    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    no_certificado = fields.Char(
        'No. Certificate', size=64, copy=False,
        help='Number of serie of certificate used for the invoice',
    )
    certificado = fields.Text(
        'Certificate', size=64, copy=False,
        help='Certificate used in the invoice',
    )
    sello = fields.Text('Stamp', size=512, copy=False, help='Digital Stamp')
    cadena_original = fields.Text(
        'String Original', size=512, copy=False,
        help='Data stream with the information contained in the electronic'
        ' invoice',
    )
    cfdi_folio_fiscal = fields.Char(
        'CFD-I Folio Fiscal', size=64, copy=False,
        help='Folio used in the electronic invoice',
        related="l10n_mx_edi_cfdi_uuid"
    )
    date_payroll = fields.Datetime(
        'Payroll Date', readonly=True,
        states={'draft': [('readonly', False)]}, index=True,
        help='Keep empty to use the current date',
        default=(fields.Datetime.now)
    )
    payment_type = fields.Many2one(
        'l10n_mx_edi.payment.method',
        help='Indicates the way it was paid or will be paid the invoice,'
        'where the options could be: check, bank transfer, reservoir in '
        'account bank, credit card, cash etc. If not know as will be '
        'paid the invoice, leave empty and the XML show “Unidentified”.',
        default=lambda self:
        self.env['l10n_mx_edi.payment.method'].search([('code', '=', '01')],
                                                      limit=1) or ''
    )
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, readonly=True,
        states={'draft': [('readonly', False)]}, track_visibility='always',
        default=lambda self: self._default_currency_id(),
    )
    cfdi_fecha_timbrado = fields.Datetime(
        'CFD-I Date Stamping', copy=False,
        help='Date when is stamped the electronic invoice',
    )
    cfdi_sello = fields.Text(
        'CFD-I Stamp', copy=False, help='Sign assigned by the SAT',
    )
    cfdi_cadena_original = fields.Text(
        'CFD-I Original String', copy=False,
        help='Original String used in the electronic invoice',
    )
    cfdi_no_certificado = fields.Char(
        'SAT CFDI Certificado', copy=False,
        help='SAT Certificate used for sign current file',
    )
    date_tz = fields.Datetime(
        compute='_compute_date_tz', string='Date Payroll with TZ',
        help='Date of Invoice with Time Zone',
    )
    antiquity = fields.Integer(
        compute='_compute_antiquity', help='Antiquity in weeks',
    )
    total_days = fields.Integer(
        compute='_compute_total_days',
        help='Helper field to compute the total days included in payslip',
    )
    cfdi_nomina = fields.Binary()
    cfdi_nomina_file_name = fields.Char()
    # name = vat + '_' + payslip.number + '.' + mimetype
    source_resource = fields.Selection([
        ('IP', 'Own income'),
        ('IF', 'Federal income'),
        ('IM', 'Mixed income')],
        help='Used in XML to identify the source of the resource used '
        'for the payment of payroll of the personnel that provides or '
        'performs a subordinate or assimilated personal service to salaries '
        'in the dependencies. This value will be set in the XML attribute '
        '"OrigenRecurso" to node "EntidadSNCF".')
    amount_sncf = fields.Float(
        'Own resource', help='When the attribute in "Source Resource" is "IM" '
        'this attribute must be added to set in the XML attribute '
        '"MontoRecursoPropio" in node "EntidadSNCF", and must be less that '
        '"TotalPercepciones" + "TotalOtrosPagos"')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
        ('canceled', 'Cancelado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio',
                                        copy=False,
                                        readonly=True,
                                        help='''Folio in electronic invoice,
                                                 is returned by SAT
                                                 when send to stamp.''',
                                        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi = fields.Binary(string='Cfdi content',
                                     copy=False,
                                     readonly=True,
                                     help='The cfdi xml content encoded in base64.',
                                     related='cfdi_nomina')
    l10n_mx_edi_cfdi_supplier_rfc = fields.Char(string='Supplier RFC',
                                                copy=False,
                                                readonly=True,
                                                help='''The supplier tax
                                                 identification number.''',
                                                compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_customer_rfc = fields.Char(string='Customer RFC',
                                                copy=False,
                                                readonly=True,
                                                help='''The customer tax
                                                identification number.''',
                                                compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_amount = fields.Monetary(string='Total Amount',
                                              copy=False, readonly=True,
                                              help='''The total amount
                                              reported on the cfdi.''',
                                              compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_certificate_id = fields.Many2one('l10n_mx_edi.certificate',
                                                      string='Certificate',
                                                      copy=False, readonly=True,
                                                      help='''The certificate used during
                                                      the generation of the cfdi.''')

    l10n_mx_edi_pac_status = fields.Selection(
        selection=[
            ('retry', 'Retry'),
            ('to_sign', 'To sign'),
            ('signed', 'Signed'),
            ('to_cancel', 'To cancel'),
            ('cancelled', 'Cancelled')
        ],
        string='PAC status',
        help='Refers to the status of the invoice inside the PAC.',
        readonly=True,
        copy=False)

    l10n_mx_edi_sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'),
            ('undefined', 'Not Synced Yet'),
            ('not_found', 'Not Found'),
            ('cancelled', 'Cancelled'),
            ('valid', 'Valid'),
        ],
        string='SAT status',
        help='Refers to the status of the invoice inside the SAT system.',
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined')