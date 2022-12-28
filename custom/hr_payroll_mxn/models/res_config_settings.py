# -*- coding: utf-8 -*-

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError, except_orm
from odoo import _, api, fields, models, tools
from pytz import timezone
import base64
import logging
import ssl
import subprocess
import tempfile
from datetime import datetime
from hashlib import sha1

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except ImportError:
    _logger.warning(
        'OpenSSL library not found. If you plan to use l10n_mx_edi, please install the library from https://pypi.python.org/pypi/pyOpenSSL')


class ResConfigSettings(models.TransientModel):
    _name = "res.config.settings"
    _inherit = "res.config.settings"


    
    edi_payslip_user_bd = fields.Char(
        string = "Usuario BD",
        related="company_id.edi_payslip_user_bd",
        readonly=False,
        )
    
    edi_payslip_passw_bd = fields.Char(
        string = "Contraseña BD",
        related="company_id.edi_payslip_passw_bd",
        readonly=False
        )
    
    edi_payslip_url_bd = fields.Char(
        string = "URL BD",
        related="company_id.edi_payslip_url_bd",
        readonly=False
        )
    
    edi_payslip_name_bd = fields.Char(
        string = "Nombre BD",
        related="company_id.edi_payslip_name_bd",
        readonly=False
        )

    
    edi_payslip_user_pac = fields.Char(
        string="Usuario para PAC.",
        related="company_id.edi_payslip_user_pac",
        readonly=False
    )
    
    edi_payslip_pass_pac = fields.Char(
        string="Contraseña para PAC.",
        related="company_id.edi_payslip_pass_pac",
        readonly=False
    )
    
    edi_payslip_test_pac = fields.Boolean(
        string="Modo de Prueba",
        default=False,
        related="company_id.edi_payslip_test_pac",
        readonly=False
    )
    


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            edi_payslip_test_pac = self.env['ir.config_parameter'].sudo().get_param('hr_payroll_mxn.edi_payslip_test_pac'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        edi_payslip_test_pac = self.edi_payslip_test_pac and self.edi_payslip_test_pac or False

        param.set_param('hr_payroll_mxn.edi_payslip_test_pac', edi_payslip_test_pac)
    
    edi_payslip_fiscal_regime = fields.Selection([('601', 'General de Ley Personas Morales'),
         ('603', 'Personas Morales con Fines no Lucrativos'),
         ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios'),
         ('606', 'Arrendamiento'),
         ('607', 'Régimen de Enajenación o Adquisición de Bienes'),
         ('608', 'Demás ingresos'),
         ('609', 'Consolidación'),
         ('610',
          'Residentes en el Extranjero sin Establecimiento Permanente en México'),
         ('611', 'Ingresos por Dividendos (socios y accionistas)'),
         ('612', 'Personas Físicas con Actividades Empresariales y Profesionales'),
         ('614', 'Ingresos por intereses'),
         ('615', 'Régimen de los ingresos por obtención de premios'),
         ('616', 'Sin obligaciones fiscales'),
         ('620',
          'Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
         ('621', 'Incorporación Fiscal'),
         ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
         ('623', 'Opcional para Grupos de Sociedades'),
         ('624', 'Coordinados'),
         ('628', 'Hidrocarburos'),
         ('629',
          'De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales'),
         ('630', 'Enajenación de acciones en bolsa de valores')],
        string="Regimen Fiscal",
        help="It is used to fill Mexican XML CFDI"
        "Comprobante.Emisor.RegimenFiscal.",
        related='company_id.edi_payslip_fiscal_regime', readonly=False,
        )