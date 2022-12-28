import base64
import logging
import time
import babel
import xmlrpc.client
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta
from os import path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pytz import timezone
from lxml import etree, objectify
from suds.client import Client
from odoo.addons.l10n_mx_edi.models import account_move
from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from .safe_eval import ast, Transformer
from .jinja_extension import RaiseExtension
from itertools import groupby
# from odoo.addons.l10n_mx_edi.tools.run_after_commit import run_after_commit
from lxml.objectify import fromstring
from odoo.tools.float_utils import float_repr
import requests
import tempfile
import json
import random
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips

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

    antiquity_format_sat = fields.Char(
        'Antiquity Format Sat',  copy=False,
        help='You can register the number of weeks or the period of years, months and days.',
    )

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
    # cfdi_no_certificado = fields.Char(
    #     'SAT CFDI Certificado', copy=False,
    #     help='SAT Certificate used for sign current file',
    # )
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
    cfdi_nomina = fields.Binary(copy=False)
    cfdi_nomina_file_name = fields.Char(copy=False)
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

    def antiquity_format(self):
        for rec in self:
            val = rec.employee_id.first_contract_date - rec.date_to
            date1 = rec.employee_id.first_contract_date 
            date2 = rec.date_to
            diff = relativedelta.relativedelta(date2, date1)
            years = diff.years
            months = diff.months
            days = diff.days
            print('{} years {} months {} days'.format(years, months, days))

            if years > 0 and months > 0 and days > 0:
                rec.antiquity_format_sat = str("P") +  str(years) + str("Y") + str(months) + str("M") + str(days) + str("D")
            elif years == 0 and months > 0 and days > 0:
                rec.antiquity_format_sat = str("P")  + str(months) + str("M") + str(days) + str("D")
            elif years == 0 and months == 0 and days > 0:
                rec.antiquity_format_sat = str("P") + str(days) + str("D")  


    #@api.model
    def _l10n_mx_edi_xmarts_info(self):
        # test = company_id.l10n_mx_edi_pac_test_env
        # username = company_id.l10n_mx_edi_pac_username
        # password = company_id.l10n_mx_edi_pac_password
        url = 'http://ws.facturacionmexico.com.mx/pac/?wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'DEMO700101XXX' if self.company_id.edi_payslip_test_pac == True else self.company_id.edi_payslip_user_pac,
            'password': 'DEMO700101XXX' if self.company_id.edi_payslip_test_pac == True else self.company_id.edi_payslip_pass_pac,
            'production': 'NO' if self.company_id.edi_payslip_test_pac == True else 'SI',
        }




    def sign_payslip_x(self):
        for rec in self:

            def tax_name(t): return {
            'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(t, False)
            
            # time_invoice = self.env['einvoice.edi.certificate'].sudo().get_mx_current_datetime()
            time_invoice = self.env['l10n_mx_edi.certificate'].sudo().get_mx_current_datetime()
            vals = self._get_datas()
            self.antiquity_format()
            print("******",vals)
            total_percepciones = vals['total_percepciones']
            total_otrospagos = vals['total_otrospagos']
            total_deducciones = vals['total_deducciones']

            Percepcion = []
            for line in rec.line_ids:
                print("*****   Percepcion   ******", line.category_id.code)
                if line.category_id.code == 'PERGRA':
                    if line.taxable_amount > 0 or line.total - line.taxable_amount > 0:
                        Percepcion.append({
                            'TipoPercepcion': '001',#line.salary_rule_id.code_sat,
                            'Clave': str("000")+str(line.code),
                            'Concepto': line.name,
                            'ImporteGravado': '{:.2f}'.format(line.taxable_amount) if  line.taxable_amount > 0 else {}, 
                            'ImporteExento': '{:.2f}'.format(line.total - line.taxable_amount) if  line.total - line.taxable_amount > 0 else {},
                        })
                        if line.salary_rule_id.code_sat == '019':
                            Percepcion.append({
                                'nomina12:HorasExtra':{
                                    'Dias': 0,
                                    'TipoHoras': line.salary_rule_id.overtime_type_id.code,
                                    'HorasExtra': 0,
                                    'ImportePagado': '{:.2f}'.format(line.total),
                                }
                                })
            print("---------------------------------------------------------",Percepcion)
            Deducciones = []
            if total_deducciones > 0:
                Deducciones.append({
                    'TotalImpuestosRetenidos': '{:.2f}'.format(vals['TotalImpuestosRetenidos']),
                    'TotalOtrasDeducciones': '{:.2f}'.format(vals['total_other_ded']),
                                
                    })
                for line in rec.line_ids:
                    if line.category_id.code == 'DEDC' and line.total:
                        Deducciones.append({
                            'nomina12:Deduccion': {
                                    'TipoDeduccion': line.salary_rule_id.code_sat,
                                    'Clave': line.code,
                                    'Concepto': line.name,
                                    'Importe': '{:.2f}'.format(line.total),
                                }
                            })
            OtrosPagos = []
            if vals['has_other']:
                for line in payslip.line_ids:
                    if line.category_id.code == 'OTROS':
                        OtrosPagos.append({
                            'nomina12:OtroPago':{
                                    'TipoOtroPago': line.salary_rule_id.salary_payment_type_id.code,
                                    'Clave': line.code,
                                    'Concepto': line.name,
                                    'Importe': '{:.2f}'.format(line.total),
                                    
                                },
                            })
                        if line.salary_rule_id.code == 'ISRSUB':
                            OtrosPagos.append({
                                'nomina12:SubsidioAlEmpleo':{
                                        'SubsidioCausado': '{:.2f}'.format(line.total),
                                    },
                                })
            xml_json = {'xmlns:cfdi': 'http://www.sat.gob.mx/cfd/3',
                        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                        'xsi:schemaLocation': 'http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv32.xsd http://www.sat.gob.mx/nomina12 http://www.sat.gob.mx/sitio_internet/cfd/nomina/nomina12.xsd',
                        'xmlns:nomina12': 'http://www.sat.gob.mx/nomina12',
                        'Version': '3.3',
                        'Serie': 'NOMINA',
                        'Folio': rec.number or 'N/A',
                        'Fecha': time_invoice.strftime('%Y-%m-%dT%H:%M:%S'),
                        'TipoDeComprobante': 'N',
                        'FormaPago': '99',
                        'MetodoPago': 'PUE',
                        'NoCertificado': '',
                        'Certificado': '',
                        'SubTotal': '{:.2f}'.format(total_percepciones + total_otrospagos),
                        'Total': '{:.2f}'.format(total_percepciones + total_otrospagos - total_deducciones),
                        'LugarExpedicion': rec.company_id.partner_id.zip,
                        'Moneda': 'MXN',
                        'Sello': '',
                        'cfdi:Emisor':{
                            'Rfc':rec.company_id.partner_id.vat,
                            'Nombre':rec.company_id.name,
                            'RegimenFiscal':rec.company_id.l10n_mx_edi_fiscal_regime
                        },

                        'cfdi:Receptor':{
                            'Rfc': rec.employee_id.vat,
                            'Nombre': rec.employee_id.name,
                            'UsoCFDI': 'P01'
                        },
                        'cfdi:Conceptos': {
                            'cfdi:Concepto': {
                                'Cantidad': '1',
                                'Descripcion': 'Pago de nómina',
                                'ValorUnitario': '{:.2f}'.format(total_percepciones + total_otrospagos),
                                'Importe': '{:.2f}'.format(total_percepciones + total_otrospagos),
                                'ClaveProdServ': '84111505',
                                'ClaveUnidad': 'ACT',
                                'Descuento': total_deducciones if total_deducciones > 0 else {}
                            }
                        },

                        'cfdi:Complemento': {
                            'nomina12:Nomina': {
                                'Version': '1.2',
                                'TipoNomina': rec.struct_id.payslip_type_id.code,
                                'FechaPago': rec.date_tz.strftime('%Y-%m-%d'),
                                'FechaInicialPago': rec.date_from.strftime('%Y-%m-%d'), #if rec.struct_id.payslip_type_id.code == 'O' else {},
                                'NumDiasPagados': '{:.3f}'.format(rec.total_days), #if rec.struct_id.payslip_type_id.code == 'O' else {},
                                'FechaFinalPago': rec.date_to.strftime('%Y-%m-%d'), # if rec.struct_id.payslip_type_id.code != 'O' else {},
                                'TotalPercepciones': '{:.2f}'.format(total_percepciones) if total_percepciones else {}, #if rec.struct_id.payslip_type_id.code != 'O' else {},
                                #'TotalDeducciones': '{:.2f}'.format(total_deducciones) if total_deducciones else {},
                                #'TotalOtrosPagos': '{:.2f}'.format(total_otrospagos) if total_otrospagos else {},
                            
                            'nomina12:Emisor': {
                                'RegistroPatronal': rec.company_id.patron_registration if rec.contract_id.type_id.code != '09' and rec.contract_id.type_id.code != '10' else {},
                                'Curp': rec.company_id.curp if rec.company_id.l10n_mx_edi_fiscal_regime == '612' else {},
                                # 'nomina12:EntidadSNCF': {
                                #     'OrigenRecurso': rec.source_resource if rec.source_resource else {},
                                #     'MontoRecursoPropio': '{:.2f}'.format(rec.amount_sncf) if rec.amount_sncf else {},
                                # }
                            },
                            'nomina12:Receptor': {
                                'Curp': rec.employee_id.curp,
                                'TipoContrato': rec.contract_id.type_id.code,
                                'TipoRegimen': rec.contract_id.tipo_regimen.clave,
                                'NumEmpleado': rec.employee_id.work_number,
                                'Departamento': rec.employee_id.department_id.name if rec.employee_id.department_id else {},
                                'Puesto': rec.employee_id.job_id.name if rec.employee_id.job_id else '',
                                'PeriodicidadPago': rec.contract_id.isr_table.code if rec.struct_id.payslip_type_id.code == 'O' else '99',
                                'Banco': 0 if rec.payment_type and rec.payment_type.name == '03' else {},
                                #'Banco': rec.employee_id.bank_account_id.bank.sat_code,
                                'ClaveEntFed': rec.company_id.partner_id.state_id.code,
                                'NumSeguridadSocial': rec.employee_id.ssnid if rec.contract_id.type_id.code != '09' and rec.contract_id.type_id.code != '10' else {},
                                'FechaInicioRelLaboral': rec.contract_id.date_start if rec.contract_id.type_id.code != '09' and rec.contract_id.type_id.code != '10' else {},
                                'Antigüedad': rec.antiquity_format_sat if rec.contract_id.type_id.code != '09' and rec.contract_id.type_id.code != '10' else {},
                                'RiesgoPuesto': rec.contract_id.riesgo_puesto.clave,
                                'Sindicalizado': "Si" if rec.employee_id.syndicated else {},
                                'SalarioBaseCotApor': '{:.2f}'.format(rec.contract_id.integrated_wage) if rec.contract_id.type_id.code != '09' and rec.contract_id.type_id.code != '10' else {},
                                'SalarioDiarioIntegrado': '{:.2f}'.format(rec.contract_id.integrated_wage) if rec.contract_id.type_id.code != '09' and rec.contract_id.type_id.code != '10' else {},
                            },
                            'nomina12:Percepciones': {
                                'TotalGravado': '{:.2f}'.format(vals['percepciones_totalgravado']) if vals['percepciones_totalgravado'] > 0 else {},
                                'TotalExento': '{:.2f}'.format(vals['percepciones_totalexento']) if vals['percepciones_totalexento'] > 0 else {},
                                'TotalSueldos': '{:.2f}'.format(vals['percepciones_totalgravado'] + vals['percepciones_totalexento']) if vals['percepciones_totalgravado'] + vals['percepciones_totalexento'] > 0 else {},
                                'nomina12:Percepcion':Percepcion,
                            },

                            'nomina12:Deducciones': Deducciones if Deducciones else [],
                            'nomina12:OtrosPagos': OtrosPagos if OtrosPagos else [],
                           
                        }
                        }

                        }
            print("JSON: ", xml_json)
            # rec.edi_cfdi_supplier_rfc = rec.company_id.vat
            # rec.edi_cfdi_customer_rfc = rec.partner_id.vat
            # rec.edi_cfdi_amount = '%0.*f' % (2, float(amount_untaxed) - float(float('%.*f' % (2, total_discount)) or 0) + (
            #                                     float(total_transferred) or 0) - (float(total_withhold) or 0))
            try:
                user_data = rec._l10n_mx_edi_xmarts_info()
                url = rec.company_id.edi_payslip_url_bd
                db = rec.company_id.edi_payslip_name_bd
                username = rec.company_id.edi_payslip_user_bd
                password = rec.company_id.edi_payslip_passw_bd
                print("------   ,url,db,username,password   -----",url,db,username,password)
                common = xmlrpc.client.ServerProxy(
                    '{}/xmlrpc/2/common'.format(url))
                uid = common.authenticate(db, username, password, {})
                models = xmlrpc.client.ServerProxy(
                    '{}/xmlrpc/2/object'.format(url))
                response = {}
                
                
                model_name = 'sign.account.move'
                print("xxxxxxxxxxxxxxxxxxxxxxxx",user_data['username'], user_data['password'], user_data['production'])
                response = models.execute_kw(db, uid, password, model_name,'request_sign_invoice', [False, xml_json, user_data['username'], user_data['password'], user_data['production'],'N'])
                print("xxxxxxxxxxxxxxxxxxxxxxxx",response)
                rec._edi_post_sign_process(
                    response['xml'], response['code'], response['msg'])
                if response['xml'] != '':
                    #rec.edi_cfdi_uuid = response['uuid']
                    #rec.cfdi_nomina_file_name = 'xxxx.xml'
                        # ('%s-%s-MX-Invoice-%s.xml' %
                        #     (rec.journal_id.code, rec.name,
                        #     "3.3".replace('.', '-'))).replace('/', '')
                    #rec.edi_pac_status = 'signed'
                    #rec.edi_cadena_original = response['cadena']
                    print("zzzz")
                    vat = self.company_id.vat
                    name = vat + '_' + self.number + '.xml'
                    print("************",name)
                    self.cfdi_nomina_file_name = name
                    self.create_ir_attachment_facturae()

                
            except Exception as err:
                rec.message_post(body=_(
                    """<p>La conexion falló.</p><p><ul>%s</ul></p>""" % err))
                #rec.edi_pac_status = 'retry'

    def _edi_post_sign_process(self, xml_signed, code=None, msg=None):
        self.ensure_one()
        if xml_signed:
            print("--------------xml_signed-----------------------",xml_signed)
            body_msg = _('The sign service has been called with success')
            #self.edi_pac_status = 'signed'
            self.cfdi_nomina = False
            self.cfdi_nomina = xml_signed
            post_msg = []
        else:
            body_msg = _('The sign service requested failed')
            post_msg = []
            #self.edi_pac_status = 'retry'
        if code:
            post_msg.extend([_('Code: %s') % code])
        if msg:
            post_msg.extend([_('Message: %s') % msg])
        self.message_post(
            body=body_msg + create_list_html(post_msg),
            message_type='notification')



    def l10n_mx_edi_xmarts_sign(self):
        # n_random = random.randrange(1,10)
        url = 'http://pac10.facturacionmexico.com.mx/pac/?wsdl '# % n_random

        cfdi = base64.decodestring(self.cfdi_nomina)
        ress = None
        response = None
        client = Client(url)

        response = client.service.timbrar33b64(
            rfc='DEMO700101XXX', clave='DEMO700101XXX', xml=self.cfdi_nomina.decode('utf-8'), produccion='NO')
        print("RESPONSE: ", response)
        if response['codigo_mf_texto'] != 'SALDO INSUFICIENTE':
            ress = json.loads(response['mensaje_original_pac_json'])
            if ress['status'] == 'success':
                xmltfd = ress['data']['tfd']
                cfdi_d = cfdi.decode('utf-8')

                xmlstr = str(cfdi_d[:-20])+"<cfdi:Complemento>" + \
                    str(xmltfd[38:])+"</cfdi:Complemento>"+str(cfdi_d[-20:])

                xml_signed = xmlstr.encode('utf-8') or None
                print("XML RESPONSE: \n ", response['cfdi'])
                print("XML RESPONSE: \n ", xmlstr)
                if xml_signed:
                    xml_signed = base64.b64encode(xml_signed)
                    values = {
                        'cfdi': response['cfdi'],
                        'png': response['png'],
                        'mensaje_original_pac_json': response['mensaje_original_pac_json'],
                        'uuid': response['uuid'],
                        'status': json.loads(response['mensaje_original_pac_json'])['status'],
                        'codigo': response['codigo_mf_numero'],
                        'cadena': cadena
                    }
                    return values
            else:
                values = {
                    'mensaje_original_pac_json': response['mensaje_original_pac_json'],
                    'status': json.loads(response['mensaje_original_pac_json'])['status'],
                    'codigo': response['codigo_mf_numero']
                }
                return values
        else:
            values = {
                'mensaje_original_pac_json': response['codigo_mf_texto'],
                'status': 'error',
                'codigo': response['codigo_mf_numero']
            }
            print("VALUES 0 : ", values)
            return values









    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        """
        :returns: a list of dict containing the worked days values that should be applied for the given payslip
        """
        res = []
        # fill only if the contract as a working schedule linked
        self.ensure_one()
        contract = self.contract_id
        if contract.resource_calendar_id:
            res = self._get_worked_day_lines_values(domain=domain)
            if not check_out_of_contract:
                return res

            # If the contract doesn't cover the whole month, create
            # worked_days lines to adapt the wage accordingly
            out_days, out_hours = 0, 0
            reference_calendar = self._get_out_of_contract_calendar()
            if self.date_from < contract.date_start:
                start = fields.Datetime.to_datetime(self.date_from)
                stop = fields.Datetime.to_datetime(contract.date_start) + relativedelta(days=-1, hour=23, minute=59)
                out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False)
                out_days += out_time['days']
                out_hours += out_time['hours']
            if contract.date_end and contract.date_end < self.date_to:
                start = fields.Datetime.to_datetime(contract.date_end) + relativedelta(days=1)
                stop = fields.Datetime.to_datetime(self.date_to) + relativedelta(hour=23, minute=59)
                out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False)
                out_days += out_time['days']
                out_hours += out_time['hours']

            if out_days or out_hours:
                work_entry_type = self.env['hr.work.entry.type'].search([('code','=','WORK100')], limit=1)#self.env.ref('hr_payroll.hr_work_entry_type_out_of_contract')
                res.append({
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'number_of_days': out_days,
                    'number_of_hours': out_hours,
                })
        return res

    

    # TODO move this function into hr_contract module, on hr.employee object
    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    def _get_payslip_lines(self):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = localdict['categories'].dict.get(category.code, 0) + amount
            return localdict

        self.ensure_one()
        result = {}
        rules_dict = {}
        worked_days_dict = {line.code: line for line in self.worked_days_line_ids if line.code}
        inputs_dict = {line.code: line for line in self.input_line_ids if line.code}

        employee = self.employee_id
        contract = self.contract_id

        localdict = {
            **self._get_base_local_dict(),
            **{
                'categories': BrowsableObject(employee.id, {}, self.env),
                'rules': BrowsableObject(employee.id, rules_dict, self.env),
                'payslip': Payslips(employee.id, self, self.env),
                'worked_days': WorkedDays(employee.id, worked_days_dict, self.env),
                'inputs': InputLine(employee.id, inputs_dict, self.env),
                'employee': employee,
                'contract': contract
            }
        }
        for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
            localdict.update({
                'result': None,
                'result_qty': 1.0,
                'result_rate': 100})
            if rule._satisfy_condition(localdict):
                amount, qty, rate = rule._compute_rule(localdict)
                #check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                #set/overwrite the amount computed for this rule in the localdict
                tot_rule = amount * qty * rate / 100.0
                localdict[rule.code] = tot_rule
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                # create/overwrite the rule in the temporary results

                taxable_amount = rule.compute_tax(localdict,rule)

                result[rule.code] = {
                    'sequence': rule.sequence,
                    'code': rule.code,
                    'name': rule.name,
                    'note': rule.note,
                    'salary_rule_id': rule.id,
                    'contract_id': contract.id,
                    'employee_id': employee.id,
                    'amount': amount,
                    'quantity': qty,
                    'rate': rate,
                    'slip_id': self.id,
                    'taxable_amount': taxable_amount,
                }
        return result.values()



    # @api.multi
    def l10n_mx_edi_update_sat_status(self):
        '''Synchronize both systems: Odoo & SAT to make sure the invoice is valid.
        '''
        url = '''https://consultaqr.facturaelectronica.sat.gob.mx/
        ConsultaCFDIService.svc?wsdl'''
        headers = {'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta',
                   'Content-Type': 'text/xml; charset=utf-8'}
        template = """<?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/" xmlns:ns1="
    http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/
    XMLSchema-instance"
     xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
       <SOAP-ENV:Header/>
       <ns1:Body>
          <ns0:Consulta>
             <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
          </ns0:Consulta>
       </ns1:Body>
    </SOAP-ENV:Envelope>"""
        namespace = {'a': '''http://schemas.datacontract.org/2004/07/
        Sat.Cfdi.Negocio.ConsultaCfdi.Servicio'''}
        for inv in self.filtered('cfdi_nomina'):
            supplier_rfc = inv.company_id.vat
            customer_rfc = inv.employee_id.vat
            total = float_repr(inv.l10n_mx_edi_cfdi_amount,
                               precision_digits=inv.currency_id.decimal_places)
            uuid = inv.l10n_mx_edi_cfdi_uuid
            params = '?re=%s&amp;rr=%s&amp;tt=%s&amp;id=%s' % (
                tools.html_escape(tools.html_escape(supplier_rfc or '')),
                tools.html_escape(tools.html_escape(customer_rfc or '')),
                total or 0.0, uuid or '')
            soap_env = template.format(data=params)
            try:
                soap_xml = requests.post(url, data=soap_env,
                                         headers=headers, timeout=20)
                response = fromstring(soap_xml.text)
                status = response.xpath(
                    '//a:Estado', namespaces=namespace)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            inv.l10n_mx_edi_sat_status = CFDI_SAT_QR_STATE.get(
                status[0] if status else '', 'none')

    # @api.multi
    def l10n_mx_edi_log_error(self, message):
        self.ensure_one()
        self.message_post(body=_('Error during the process: %s') % message,
                          type='notification')

    # @api.onchange('cfdi_nomina')
    # def onchange_cfdi_nomina_name(self):
    #     if self.id:
    #         data = {
    #             'model': 'hr.payslip',
    #             'id': self.id,
    #             'report_type': 'aeroo',
    #         }
    #         result, mimetype = self.render_report(
    #             self._cr, self._uid, [self.id],
    #             'payroll_report_aeroo', data, context=self._context,
    #         )
    #         vat = self.company_id.partner_id.vat_split
    #         name = vat + '_' + self.number + '.' + mimetype
    #         self.cfdi_nomina_file_name = name

    @api.onchange('cfdi_nomina')
    def onchange_read_xml_uuid(self):
        for rec in self:
            if rec.cfdi_nomina:
                result = rec.cfdi_nomina.encode('utf-8')
                data = base64.decodestring(result)
                fobj = tempfile.NamedTemporaryFile(delete=False)
                fname = fobj.name
                fobj.write(data)
                fobj.close()
                file_xml = open(fname, "r")
                tree = objectify.fromstring(file_xml.read().encode())
                if rec._get_stamp_data(tree) is None:
                    rec.l10n_mx_edi_cfdi_uuid = ''
                else:
                    tfd = rec._get_stamp_data(tree)
                    tfd = rec._get_stamp_data(tree)
                    rec.l10n_mx_edi_cfdi_uuid = tfd.get('UUID')
                    rec.l10n_mx_edi_cfdi_amount = tree.get('Total', tree.get('total'))

            else:
                rec.l10n_mx_edi_cfdi_uuid = ''

    @api.model
    def l10n_mx_edi_get_xml_etree(self, cfdi=None):

        self.ensure_one()
        if cfdi is None and self.l10n_mx_edi_cfdi:
            cfdi = base64.decodestring(self.l10n_mx_edi_cfdi)
        if cfdi is None:
            return None
        else:
            return cfdi
        # return None


    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        '''Get the TimbreFiscalDigital node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        '''
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    # @api.multi
    @api.depends('cfdi_nomina', 'l10n_mx_edi_cfdi', 'l10n_mx_edi_cfdi_uuid')
    def _compute_cfdi_values(self):
        '''Fill the invoice fields from the cfdi values.
        '''
        for inv in self:
            attachment_id = inv.l10n_mx_edi_retrieve_last_attachment()
            if attachment_id:
                datas = attachment_id._file_read(attachment_id.store_fname)
                # inv.cfdi_nomina = datas
                cfdi = base64.decodestring(datas).replace(
                    b'xmlns:schemaLocation', b'xsi:schemaLocation')
                
                if not cfdi:
                    tree = fromstring(inv.l10n_mx_edi_get_xml_etree(cfdi))
                    # if already signed, extract uuid
                    tfd_node = inv.l10n_mx_edi_get_tfd_etree(tree)
                    if tfd_node is not None:
                        inv.l10n_mx_edi_cfdi_uuid = tfd_node.get('UUID')
                    else:
                        inv.l10n_mx_edi_cfdi_uuid = ''
                    inv.l10n_mx_edi_cfdi_amount = tree.get('Total', tree.get('total')) or 0
                    inv.l10n_mx_edi_cfdi_supplier_rfc = tree.Emisor.get(
                        'Rfc', tree.Emisor.get('rfc'))
                    inv.l10n_mx_edi_cfdi_customer_rfc = tree.Receptor.get(
                        'Rfc', tree.Receptor.get('rfc')) or ''
                    certificate = tree.get('noCertificado', tree.get('NoCertificado'))
                    inv.l10n_mx_edi_cfdi_certificate_id = self.env['l10n_mx_edi.certificate']\
                        .sudo().search(
                        [('serial_number', '=', certificate)], limit=1) or ''
                else:
                    inv.l10n_mx_edi_cfdi_uuid = ''
                    inv.l10n_mx_edi_cfdi_supplier_rfc = ''
                    inv.l10n_mx_edi_cfdi_customer_rfc = ''
                    inv.l10n_mx_edi_cfdi_amount = 0
            else:
                inv.l10n_mx_edi_cfdi_uuid = ''
                inv.l10n_mx_edi_cfdi_supplier_rfc = ''
                inv.l10n_mx_edi_cfdi_customer_rfc = ''
                inv.l10n_mx_edi_cfdi_amount = 0

    # @api.multi
    def _compute_date_tz(self):
        for record in self.filtered('date_payroll'):
            record.date_tz = timezone('America/Mexico_City').localize(
                record.date_payroll).strftime('%Y-%m-%d %H:%M:%S')

    # @api.multi
    def _compute_antiquity(self):
        for record in self.filtered('contract_id.date_start'):
            begin = record.contract_id.date_start
            end = record.date_to + timedelta(days=1)
            record.antiquity = (end - begin).days / 7

    # @api.multi
    def _compute_total_days(self):
        for record in self:
            total_days = 0
            for days in record.worked_days_line_ids:
                total_days += days.number_of_days
            record.total_days = total_days


    # @api.multi
    def _get_imss(self, fee_name='c_obrera'):
        for rec in self:
            # Calculate amount to pay for IMSS according to actual IMSS tables
            # pylint: disable=eval-used,unused-variable
            result = 0
            print("FEE NAME:  ", fee_name)
            transformer = Transformer()
            # smgvdf = self.env['hr.payroll'].search(  # noqa: F841
            #     [('date_start', '<=', rec.date_from)], limit=1,
            #     order='date_start desc',
            # ).smgvdf
            # sbc = rec.contract_id.integrated_wage  # noqa: F841
            total_days = rec.contract_id.isr_table.number_of_days
            imss_table = self.env['imss.table'].search([])
            suma = sum([x for x in imss_table.mapped(fee_name)])
            # for row in imss_table:
            #     tree = ast.parse(row.base, mode='eval')
            #     # raises RuntimeError on invalid code
            #     transformer.visit(tree)

            #     # compile the ast into a code object
            #     clause = compile(tree, '<AST>', 'eval')

            #     # and eval the compiled object
            #     base = eval(clause)
            #     if base > 0:
            #         fee = getattr(row, fee_name)
            #         result = result + base * (fee / 100) * total_days
            result = (suma / 15) * total_days
            return result


    # @api.multi
    def cancel_done_sheet(self):
        """ Cancel payslip on SAT and also cancel payslip """
        # cfdi_obj =self.env['account.move']
        # cfdi_obj = self.env['ir.attachment']
        for payslip in self:
            # First we are going to try cancel the payslip, and only when
            # the payslip is properly cancelled then we try to cancel the
            # cfdi on SAT

            # Se comento la siguiente linea para corregir error al cancelar status
            # payslip.cancel_sheet()

            # Se agrega lo siguiente en lugar de la linea anterior
            # self.write({'state': 'canceled'})

            # Search for cfdis to cancel on SAT
            # cfdis = cfdi_obj.search([
            #     ('res_id', '=', payslip.id),
            #     ('res_model', '=', 'hr.payslip'),
            # ])
            # for cfdi in cfdis:
            #     if cfdi.state != 'cancel':
            #         cfdi.signal_cancel([cfdi.id])
            # self.action_cancel_cfdi()
            self._l10n_mx_edi_cancel()
            self.l10n_mx_edi_update_pac_status()
            if self.l10n_mx_edi_pac_status == 'cancelled':
                self.write({'state': 'canceled'})

    # @api.multi
    def l10n_mx_edi_update_pac_status(self):
        '''Synchronize both systems: Odoo & PAC if the invoices need to be signed or cancelled.
        '''
        for record in self:
            if record.l10n_mx_edi_pac_status in ('to_sign', 'retry'):
                record._l10n_mx_edi_retry()
            elif record.l10n_mx_edi_pac_status == 'to_cancel':
                record._l10n_mx_edi_cancel()

    # @api.multi
    def _l10n_mx_edi_cancel(self):
        '''Call the cancel service with records that can be signed.
        '''
        records = self.search([
            ('l10n_mx_edi_pac_status', 'in',
                ['to_sign', 'signed', 'to_cancel', 'retry']),
            ('id', 'in', self.ids)])
        for record in records:
            if record.l10n_mx_edi_pac_status in ['to_sign', 'retry']:
                record.l10n_mx_edi_pac_status = False
                record.message_post(body=_('''The cancel service has been
                    called with success'''))
            else:
                record.l10n_mx_edi_pac_status = 'to_cancel'
        records = self.search([
            ('l10n_mx_edi_pac_status', '=', 'to_cancel'),
            ('id', 'in', self.ids)])
        #records._l10n_mx_edi_call_service('cancel')

    def action_cancel_cfdi(self):
        msg = ''
        folio_cancel = ''
        uuids = []
        pac_params_obj = self.env['params.pac']
        for inv in self:
            certificate_id = inv.company_id.certificate_id
            if not certificate_id:
                inv.message_post(body=_(
                    'No tienes definido certificado para esta compañia!'))
                continue
            pac_params = pac_params_obj.search([
                ('method_type', '=', 'cancelar'),
                ('company_id', '=', inv.company_id.id),
            ], limit=1)
            if not pac_params:
                inv.message_post(body=_(
                    'No tienes parametros del PAC configurados para '
                    'cancelar'))
                continue
            pac_usr = pac_params.user
            pac_pwd = pac_params.password
            wsdl_url = pac_params.url_webservice
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.cer_file)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key_file, certificate_id.password)).decode('UTF-8')
            try:
                client = Client(wsdl_url, cache=None)
            except:
                inv.message_post(body=_(
                    'Revisa tu conexion a internet y los datos del PAC'))
                continue
            taxpayer_id = inv.company_id.partner_id.vat
            folio_cancel = inv.cfdi_folio_fiscal
            uuids.append(folio_cancel)
            uuids_list = client.factory.create("UUIDS")
            uuids_list.uuids.string = uuids
            result = client.service.cancel(
                uuids_list, pac_usr, pac_pwd, taxpayer_id, cer_pem, key_pem)
            time.sleep(1)
            if 'Folios' not in result:
                msg += _('%s' % result)
                inv.message_post(body=_('Mensaje %s') % (msg))
                continue
            estatus_uuid = result.Folios[0][0].EstatusUUID
            if estatus_uuid in ('201', '202'):
                msg += _(
                    '\n- El proceso de cancelación se ha completado '
                    'correctamente.\n El uuid cancelado es: ') + folio_cancel
                self.cfdi_fecha_cancelacion = time.strftime(
                    '%Y-%m-%d %H:%M:%S')
            else:
                inv.message_post(body=_('Mensaje %s %s Code: %s') % (
                    msg, result.Folios[0][0].EstatusCancelacion,
                    estatus_uuid))
            inv.message_post(body=msg)
            if 'Acuse' in result:
                cname = 'ACUSE_CANCELACION_' + inv.move_id.name + '.xml'
                self.env['ir.attachment'].create({
                    'name': cname,
                    'datas_fname': cname,
                    'datas': base64.encodestring(str(
                        result.Acuse).encode()),
                    'res_model': 'hr.payslip',
                    'res_id': inv.id,
                })

    # @api.multi
    def action_printable(self):
        attachment_obj = self.env['ir.attachment']
        ir_attach_obj = self.env['ir.attachment.facturae.mx']
        for payslip in self:
            # the value of data is in this way because the report is aeroo
            data = {
                'model': 'hr.payslip',
                'id': payslip.id,
                'report_type': 'aeroo',
            }
            result, mimetype = self.render_report(
                self._cr, self._uid, [payslip.id],
                'payroll_report_aeroo', data, context=self._context,
            )
            vat = payslip.company_id.partner_id.vat_split
            name = vat + '_' + payslip.number + '.' + mimetype
            attachment = attachment_obj.create({
                'name': name,
                'datas_fname': name,
                'datas': base64.encodestring(result),
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
            })
            ir_attach_obj.write({
                'file_xml_sign': attachment.id,
                'state': 'signed',
                'last_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return

    @api.model
    def create_ir_attachment_facturae(self):
        print("-------   create_ir_attachment_facturae    ---------")
        for payslip in self:
            payslip._get_signed_xml()
            vat = payslip.company_id.vat
            name = vat + '_' + payslip.number + '.xml'
            attachment = self.env['ir.attachment'].create({
                'name': name,
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
                'datas': self.cfdi_nomina,
                'store_fname': name,
            })
            self.cfdi_nomina_file_name = name.replace('/','_')
            payslip.message_post(
                body=_('CFDI generated'),
                attachment_ids=[attachment.id])
            # call the function which creates pdf report
            # payslip.action_printable()
        return

    def action_payslip_done(self):
        for payslip in self:
            if not payslip.date_payroll:
                payslip.date_payroll = fields.Datetime.now()
            #payslip.create_ir_attachment_facturae()
            payslip.sign_payslip_x()
        return super().action_payslip_done()

    def action_payslip_cancel(self):
        for payslip in self:
            payslip.cancel_done_sheet()
        return self.write({'state': 'cancel'})

        # @api.multi
    def _get_datas(self):
        self.ensure_one()
        # Crate an environment of jinja in the templates directory
        env = Environment(
            loader=FileSystemLoader(
                path.join(
                    path.dirname(path.abspath(__file__)), '../templates',),),
            extensions=[RaiseExtension],
            undefined=StrictUndefined, autoescape=True,
        )
        # Add custom filters
        env.filters['required_field'] = required_field
        template = env.get_template('nomina1_2.mako')

        total_percepciones_grav = 0.0
        total_percepciones_ex = 0.0
        # Iterate in each line_ids to get importeGravado and importeExento
        for line in self.line_ids:
            if line.category_id.code == 'PERGRA':
                percepcion = {
                    'tipo': line.salary_rule_id.code_sat,
                    'concepto': line.name,
                    'importegravado': line.taxable_amount,
                    'importeexento': line.total - line.taxable_amount,
                    'clave': line.code,
                }
                print("PERCEPCION: ", percepcion, line.total, line.taxable_amount)
                total_percepciones_grav += percepcion['importegravado']
                total_percepciones_ex += percepcion['importeexento']
        emitter = self.company_id
        # Covert date to a date with time zone
        date_payroll_tz = datetime.now(timezone(
            'America/Mexico_City')).strftime('%Y-%m-%dT%H:%M:%S')
        # Covert date to an adequate date
        payment_day = self.date_tz.strftime('%Y-%m-%d')
        # Create a template and pass a context
        total_percepciones = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'PERGRA').mapped('total'))
        total_deducciones = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'DEDC').mapped('total'))
        total_otrospagos = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'OTROS').mapped('total'))
        total_impuestos_retenidos = sum(self.line_ids.filtered(
            lambda l: l.salary_rule_id.code_sat == '002' and l.category_id.code == 'DEDC').mapped('total'))  # noqa
        days_overtime = lambda l: sum([w.number_of_days for w in l.payslip.id.worked_days_line_ids if w.code == l.code])  # noqa
        hours_overtime = lambda l: sum([w.number_of_hours for w in l.payslip.id.worked_days_line_ids if w.code == l.code])  # noqa
        total_other_ded = sum(self.line_ids.filtered(
            lambda l: l.salary_rule_id.code_sat != '002' and l.category_id.code == 'DEDC').mapped('total'))  # noqa
        has_other = self.line_ids.filtered(
            lambda l: l.category_id.code == 'OTROS')
        # certificate_id = self.company_id.certificate_id
        certificate_ids = self.company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        self.l10n_mx_edi_cfdi_certificate_id = certificate_id
        if not certificate_id:
            raise ValidationError(_(
                'No tienes definido certificado para esta compañia !'))
        print("*****  _errors  *****",_errors)
        xml_data = {
            'payslip':self.id,
            'emitter':emitter,
            'percepciones_totalgravado':total_percepciones_grav,
            'percepciones_totalexento':total_percepciones_ex,
            'date':date_payroll_tz,
            'payment_day':payment_day,
            'errors':_errors,
            'total_percepciones':total_percepciones,
            'total_deducciones':total_deducciones,
            'total_otrospagos':total_otrospagos,
            'TotalImpuestosRetenidos':total_impuestos_retenidos,
            'days_overtime':days_overtime,
            'hours_overtime':hours_overtime,
            'total_other_ded':total_other_ded,
            'has_other':has_other,
            'certificate':certificate_id,
            'cer_data':certificate_id.sudo().get_data()[0].decode(),
        }
        return xml_data

    # @api.multi
    def _get_cfdi_dict_data(self):
        self.ensure_one()
        # Crate an environment of jinja in the templates directory
        env = Environment(
            loader=FileSystemLoader(
                path.join(
                    path.dirname(path.abspath(__file__)), '../templates',),),
            extensions=[RaiseExtension],
            undefined=StrictUndefined, autoescape=True,
        )
        # Add custom filters
        env.filters['required_field'] = required_field
        template = env.get_template('nomina1_2.mako')

        total_percepciones_grav = 0.0
        total_percepciones_ex = 0.0
        # Iterate in each line_ids to get importeGravado and importeExento
        for line in self.line_ids:
            if line.category_id.code == 'PERGRA':
                percepcion = {
                    'tipo': line.salary_rule_id.code_sat,
                    'concepto': line.name,
                    'importegravado': line.taxable_amount,
                    'importeexento': line.total - line.taxable_amount,
                    'clave': line.code,
                }
                print("PERCEPCION: ", percepcion, line.total, line.taxable_amount)
                total_percepciones_grav += percepcion['importegravado']
                total_percepciones_ex += percepcion['importeexento']
        emitter = self.company_id
        # Covert date to a date with time zone
        date_payroll_tz = datetime.now(timezone(
            'America/Mexico_City')).strftime('%Y-%m-%dT%H:%M:%S')
        # Covert date to an adequate date
        payment_day = self.date_tz.strftime('%Y-%m-%d')
        # Create a template and pass a context
        total_percepciones = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'PERGRA').mapped('total'))
        total_deducciones = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'DEDC').mapped('total'))
        total_otrospagos = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'OTROS').mapped('total'))
        total_impuestos_retenidos = sum(self.line_ids.filtered(
            lambda l: l.salary_rule_id.code_sat == '002' and l.category_id.code == 'DEDC').mapped('total'))  # noqa
        days_overtime = lambda l: sum([w.number_of_days for w in l.payslip.id.worked_days_line_ids if w.code == l.code])  # noqa
        hours_overtime = lambda l: sum([w.number_of_hours for w in l.payslip.id.worked_days_line_ids if w.code == l.code])  # noqa
        total_other_ded = sum(self.line_ids.filtered(
            lambda l: l.salary_rule_id.code_sat != '002' and l.category_id.code == 'DEDC').mapped('total'))  # noqa
        has_other = self.line_ids.filtered(
            lambda l: l.category_id.code == 'OTROS')
        # certificate_id = self.company_id.certificate_id
        certificate_ids = self.company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        self.l10n_mx_edi_cfdi_certificate_id = certificate_id
        if not certificate_id:
            raise ValidationError(_(
                'No tienes definido certificado para esta compañia !'))
        xml_data = template.render(
            payslip=self, emitter=emitter,
            percepciones_totalgravado=total_percepciones_grav,
            percepciones_totalexento=total_percepciones_ex,
            date=date_payroll_tz,
            payment_day=payment_day,
            errors=_errors,
            total_percepciones=total_percepciones,
            total_deducciones=total_deducciones,
            total_otrospagos=total_otrospagos,
            TotalImpuestosRetenidos=total_impuestos_retenidos,
            days_overtime=days_overtime, hours_overtime=hours_overtime,
            total_other_ded=total_other_ded, has_other=has_other,
            certificate=certificate_id,
            cer_data=certificate_id.sudo().get_data()[0].decode(),
        )
        _logger.warn('Jinja XML result: %s', xml_data)
        print("DATA TYPE: ", type(xml_data))
        #self.cfdi_nomina = base64.b64encode(xml_data.encode('utf-8'))
        return True

    # @api.multi
    def _get_signed_xml(self):
        for payroll in self:
            payroll._get_cfdi_dict_data()
            payroll.set_sign_data()
            company_id = payroll.company_id.id
            copy_context = dict(self._context)
            copy_context.update({'company_id': company_id})
            # self.sign_cfdi()
            #self._l10n_mx_edi_call_service('sign')
            return True

    @api.model
    def l10n_mx_edi_retrieve_attachments(self):
        """Retrieve all the cfdi attachments generated for this payment.

        :return: An ir.attachment recordset
        """
        self.ensure_one()
        if not self.cfdi_nomina:
            return []
        vat = self.company_id.partner_id.vat
        name = vat + '_' + (self.number or '') + '.xml'
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', '=', name)]
        return self.env['ir.attachment'].search(domain)

    @api.model
    def l10n_mx_edi_retrieve_last_attachment(self):
        attachment_ids = self.l10n_mx_edi_retrieve_attachments()
        return attachment_ids and attachment_ids[0] or None

    # @run_after_commit
    # @api.multi
    def _l10n_mx_edi_call_service(self, service_type):
        """Call the right method according to the pac_name, it's info returned
        by the '_l10n_mx_edi_%s_info' % pac_name'
        method and the service_type passed as parameter.
        :param service_type: sign or cancel"""
        invoice_obj = self.env['account.move']
        # Regroup the invoices by company (= by pac)
        comp_x_records = groupby(self, lambda r: r.company_id)
        for company_id, records in comp_x_records:
            pac_name = company_id.l10n_mx_edi_pac
            if not pac_name:
                continue
            # Get the informations about the pac
            pac_info_func = '_l10n_mx_edi_%s_info' % pac_name
            service_func = '_l10n_mx_edi_%s_%s' % (pac_name, service_type)
            pac_info = getattr(invoice_obj, pac_info_func)(company_id, service_type)
            # TODO - Check multi
            for record in records:
                getattr(record, service_func)(pac_info)

    @api.model
    def _l10n_mx_edi_solfact_info(self, company_id, service_type):
        test = company_id.l10n_mx_edi_pac_test_env
        username = company_id.l10n_mx_edi_pac_username
        password = company_id.l10n_mx_edi_pac_password
        url = 'https://testing.solucionfactible.com/ws/services/Timbrado?wsdl'\
            if test else 'https://solucionfactible.com/ws/services/Timbrado?wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'testing@solucionfactible.com' if test else username,
            'password': 'timbrado.SF.16672' if test else password,
        }

    # @api.multi
    def _l10n_mx_edi_solfact_sign(self, pac_info):
        '''SIGN for Solucion Factible.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for rec in self:
            cfdi = rec.cfdi_nomina.decode('UTF-8')
            try:
                client = Client(url, timeout=20)
                response = client.service.timbrar(username, password, cfdi, False)
            except Exception as e:
                rec.l10n_mx_edi_log_error(str(e))
                continue
            msg = getattr(response.resultados[0], 'mensaje', None)
            code = getattr(response.resultados[0], 'status', None)
            xml_signed = getattr(response.resultados[0], 'cfdiTimbrado', None)
            rec._l10n_mx_edi_post_sign_process(xml_signed, code, msg)

    # @api.multi
    def _l10n_mx_edi_solfact_cancel(self, pac_info):
        '''CANCEL for Solucion Factible.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for rec in self:
            uuids = [self.cfdi_folio_fiscal]
            certificate_id = self.l10n_mx_edi_cfdi_certificate_id.sudo()
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.content)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key, certificate_id.password)).decode('UTF-8')
            key_password = certificate_id.password
            try:
                client = Client(url, timeout=20)
                response = client.service.cancelar(username,
                                                   password,
                                                   uuids,
                                                   cer_pem,
                                                   key_pem,
                                                   key_password)
            except Exception as e:
                rec.l10n_mx_edi_log_error(str(e))
                continue
            code = getattr(response.resultados[0], 'statusUUID', None)
            cancelled = code in ('201', '202')  # cancelled or previously cancelled
            # no show code and response message if cancel was success
            msg = '' if cancelled else getattr(response.resultados[0], 'mensaje', None)
            code = '' if cancelled else code
            rec._l10n_mx_edi_post_cancel_process(cancelled, code, msg)

    # @api.multi
    def _l10n_mx_edi_finkok_info(self, company_id, service_type):
        test = company_id.l10n_mx_edi_pac_test_env
        username = company_id.l10n_mx_edi_pac_username
        password = company_id.l10n_mx_edi_pac_password
        if service_type == 'sign':
            url = 'http://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl'\
                if test else 'http://facturacion.finkok.com/servicios/soap/stamp.wsdl'
        else:
            url = 'http://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl'\
                if test else 'http://facturacion.finkok.com/servicios/soap/cancel.wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'cfdi@vauxoo.com' if test else username,
            'password': 'vAux00__' if test else password}

    # @api.multi
    def _l10n_mx_edi_finkok_sign(self, pac_info):
        """SIGN for Finkok."""
        # TODO - Duplicated with the invoice one
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for rec in self:
            cfdi = rec.cfdi_nomina.decode('UTF-8')
            try:
                client = Client(url, timeout=20)
                response = client.service.stamp(cfdi, username, password)
            except Exception as e:
                rec.l10n_mx_edi_log_error(str(e))
                continue
            code = 0
            msg = None
            if response.Incidencias:
                code = getattr(response.Incidencias[0][0], 'CodigoError', None)
                msg = getattr(response.Incidencias[0][0], 'MensajeIncidencia', None)
            xml_signed = getattr(response, 'xml', None)
            if xml_signed:
                xml_signed = base64.b64encode(xml_signed.encode('utf-8'))
            rec._l10n_mx_edi_post_sign_process(xml_signed, code, msg)

    # @api.multi
    def _l10n_mx_edi_finkok_cancel(self, pac_info):
        '''CANCEL for Finkok.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for inv in self:
            uuid = inv.cfdi_nomina
            certificate_id = inv.l10n_mx_edi_cfdi_certificate_id.sudo()
            company_id = self.company_id
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.content)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key, certificate_id.password)).decode('UTF-8')
            cancelled = False
            code = False
            try:
                client = Client(url, timeout=20)
                invoices_list = client.factory.create("UUIDS")
                invoices_list.uuids.string = [uuid]
                response = client.service.cancel(invoices_list,
                                                 username,
                                                 password,
                                                 company_id.vat,
                                                 cer_pem, key_pem)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            if not hasattr(response, 'Folios'):
                msg = _('A delay of 2 hours has to be respected before to cancel')
            else:
                code = getattr(response.Folios[0][0], 'EstatusUUID', None)
                cancelled = code in ('201', '202')  # cancelled or previously cancelled
                # no show code and response message if cancel was success
                code = '' if cancelled else code
                msg = '' if cancelled else _("Cancelling got an error")
            inv._l10n_mx_edi_post_cancel_process(cancelled, code, msg)

    # @api.multi
    def _l10n_mx_edi_post_sign_process(self, xml_signed, code=None, msg=None):
        """Post process the results of the sign service.

        :param xml_signed: the xml signed datas codified in base64
        :param code: an eventual error code
        :param msg: an eventual error msg
        """
        # TODO - Duplicated
        self.ensure_one()
        if xml_signed:
            body_msg = _('The sign service has been called with success')
            # Update the pac status
            self.l10n_mx_edi_pac_status = 'signed'
            self.l10n_mx_edi_cfdi = xml_signed
            self.cfdi_nomina = xml_signed
            # Update the content of the attachment
            attachment_id = self.l10n_mx_edi_retrieve_last_attachment()
            attachment_id.write({
                'datas': xml_signed,
                'mimetype': 'application/xml'
            })
            post_msg = [_('The content of the attachment has been updated')]
        else:
            body_msg = _('The sign service requested failed')
            post_msg = []
        if code:
            post_msg.extend([_('Code: %s') % code])
        if msg:
            post_msg.extend([_('Message: %s') % msg])
        self.message_post(
            body=body_msg + account_invoice.create_list_html(post_msg))

    # @api.multi
    def sign_cfdi(self):
        invoice = self.env['account.move']
        for record in self.filtered('cfdi_nomina'):
            pac_usr = ''
            pac_pwd = ''
            pac_url = ''
            pac_params_ids = self.env['params.pac'].search([
                ('method_type', '=', 'firmar'),
                ('company_id', '=', record.company_id.id),
                ('active', '=', True)], limit=1)
            if not pac_params_ids:
                raise ValidationError(_(
                    'No tienes parametros del PAC configurados'))
            pac_usr = pac_params_ids.user
            pac_pwd = pac_params_ids.password
            pac_url = pac_params_ids.url_webservice
            client = Client(pac_url, cache=None)
            xml = [self.cfdi_nomina.decode('utf-8')]
            resultado = client.service.stamp(xml, pac_usr, pac_pwd)
            if resultado.Incidencias:
                code = getattr(resultado.Incidencias[0][0], 'CodigoError',
                               None)
                msg = getattr(resultado.Incidencias[0][0],
                              'MensajeIncidencia' if code != '301' else 'ExtraInfo', None)  # noqa
                raise ValidationError(_(' %s - %s ' % (code, msg)))

            if not resultado.Incidencias or None:
                folio_fiscal = resultado.UUID or False

                original_string = invoice._create_original_str(resultado)
                self.cfdi_nomina = base64.b64encode(resultado.xml.encode())
                self.l10n_mx_edi_cfdi = base64.b64encode(resultado.xml.encode())
                data_cfdi = {
                    'cfdi_folio_fiscal': folio_fiscal,
                    'cfdi_cadena_original': original_string,
                }
                self.write(data_cfdi)

    # @api.onchange('date_from', 'date_to')
    # def onchange_date_range(self):
    #     if self.date_from and self.date_to:
    #         self.with_context(contract=True).onchange_employee()
    #     return

    # @api.multi
    def _l10n_mx_edi_post_cancel_process(self, cancelled, code=None, msg=None):
        '''Post process the results of the cancel service.

        :param cancelled: is the cancel has been done with success
        :param code: an eventual error code
        :param msg: an eventual error msg
        '''

        self.ensure_one()
        if cancelled:
            body_msg = _('The cancel service has been called with success')
            self.l10n_mx_edi_pac_status = 'cancelled'
        else:
            body_msg = _('The cancel service requested failed')
        post_msg = []
        if code:
            post_msg.extend([_('Code: %s') % code])
        if msg:
            post_msg.extend([_('Message: %s') % msg])
        self.message_post(
            body=body_msg + create_list_html(post_msg),
            subtype='account.mt_invoice_validated')

    def set_sign_data(self):
        invoice_obj = self.env['account.move']
        for payroll in self:
            # company = payroll.company_id
            certificate_ids = self.company_id.l10n_mx_edi_certificate_ids
            certificate_id = certificate_ids.sudo().get_valid_certificate()
            if not certificate_id:
                raise ValidationError(_(
                    'No tienes definido certificado para esta compañia !'))
            xml = base64.decodestring(payroll.cfdi_nomina)
            cadena = invoice_obj.generate_cadena_original(
                xml, {'path_cadena': CFDI_XSLT_CADENA})
            # sello = certificate_id.get_sello(cadena)
            sello = certificate_id.get_encrypted_cadena(cadena)
            tree = objectify.fromstring(xml)
            tree.attrib['Sello'] = sello
            xml = etree.tostring(
                tree, pretty_print=True,
                xml_declaration=True, encoding='UTF-8')
            self.cfdi_nomina = base64.b64encode(xml)
            self.l10n_mx_edi_cfdi = base64.b64encode(xml)

    @api.model
    def _get_xml_etree(self):
        self.ensure_one()
        if self.cfdi_nomina:
            cfdi = base64.decodebytes(self.cfdi_nomina)
            return objectify.fromstring(cfdi)

    @api.model
    def _get_stamp_data(self, cfdi):
        self.ensure_one()
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
    #  Anexo hr_payroll_account/hr_apayslip  #
    ##########################################
    def _default_journal_id(self):
        # TODO: Add a way to set a journal type for payslips
        res = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1,
        )
        return res.id and res or False

    journal_id = fields.Many2one(
        'account.journal', 'Salary Journal',
        states={'draft': [('readonly', False)]}, readonly=True,
        required=True, default=lambda self: self._default_journal_id(),
    )
    move_id = fields.Many2one(
        'account.move', 'Accounting Entry', readonly=True, copy=False,
    )


    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to, calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave[:1].holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.name or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to, calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res

    # @api.model
    # def get_inputs(self, contracts, date_from, date_to):
    #     res = []

    #     structure_ids = contracts.get_all_structures()
    #     rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
    #     sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
    #     inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

    #     for contract in contracts:
    #         for input in inputs:
    #             input_data = {
    #                 'name': input.name,
    #                 'code': input.code,
    #                 'contract_id': contract.id,
    #             }
    #             res += [input_data]
    #     return res

    @api.model
    def create(self, vals):
        if 'journal_id' in self._context:
            vals.update({'journal_id': self._context.get('journal_id')})
        return super(HrPayslip, self).create(vals)

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id

        #computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        # input_line_ids = self.get_inputs(contracts, date_from, date_to)
        # input_lines = self.input_line_ids.browse([])
        # for r in input_line_ids:
        #     input_lines += input_lines.new(r)
        # self.input_line_ids = input_lines
        return


    @api.onchange('contract_id')
    def onchange_contract(self):
        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True).onchange_employee()
        self.journal_id = self.contract_id.journal_id.id or False
        return

    @api.model
    def _have_worked(self, working_calendar, employee, day):
        """
        Determine if employee have worked on a given day

        Search in hr.attendance records in order to see if employee have
        arrive to work on a given day.

        @param working_calendar: The calendar that define working days
        @type working_calendar: resource.calendar
        @param employee: The employee to test
        @type employee: hr.employee
        @param day: The day to test
        @type day: Datetime
        @return: True if employee have worked False otherwise
        @rtype: bool
        """
        have_worked = self.env['hr.attendance'].have_worked(
            working_calendar, employee, day,
        )
        return have_worked

    @api.model
    def _late_hours(self, working_calendar, employee, day):
        """
        Determine if employee arrive late to work on a given day

        @param working_calendar: The calendar that define working days
        @type working_calendar: resource.calendar
        @param employee: The employee to test
        @type employee: hr.employee
        @param day: The day to test
        @type day: Datetime
        @return: Hours employee arrives late
        @rtype: int
        """
        late_hours = self.env['hr.attendance'].late_hours(
            working_calendar, employee, day,
        )
        return late_hours

    @api.model
    def _overtime_hours(self, working_calendar, employee, day):
        """
        Determine if employee do overtime on a given day
        The function in this module is just a placeholder, other modules must
        inherit and extend.

        @param working_calendar: The calendar that define working days
        @type working_calendar: resource.calendar
        @param employee: The employee to test
        @type employee: hr.employee
        @param day: The day to test
        @type day: Datetime
        @return: Hours employee do on overtime
        @rtype: int
        """
        overtime_hours = self.env['hr.attendance'].overtime_hours(
            working_calendar, employee, day,
        )
        return overtime_hours


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    # @api.multi
    def action_payslips_done(self):
        self.ensure_one()
        for payslip in self.slip_ids.filtered(lambda p: p.state == 'draft'):
            try:
                payslip.source_resource = self.source_resource
                payslip.action_payslip_done()
            except ValidationError as ex:
                payslip.message_post(body=ex.name)

    source_resource = fields.Selection([
        ('IP', 'Own income'),
        ('IF', 'Federal income'),
        ('IM', 'Mixed income')],
        help='If this value is set will be assigned in all the payslips '
        'related.')
