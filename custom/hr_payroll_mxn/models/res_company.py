# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    patron_registration = fields.Char()
    risk_company = fields.Float(string='Prima de Riesgo')
    curp = fields.Char('CURP')

    # # @api.one
    # @api.constrains('partner_id', 'curp')
    # def _check_curp(self):
    #     """When company is "persona física" we need curp for payslips
    #     """
    #     if self.partner_id.property_account_position_id.code in ['612']:
    #         if not self.curp:
    #             raise ValidationError(
    #                 _('CURP is needed for the fiscal position you selected.'),
    #             )
    
    

    edi_payslip_user_bd = fields.Char(
        string = "Usuario BD"
        )
    edi_payslip_passw_bd = fields.Char(
        string = "Contraseña BD"
        )
    edi_payslip_url_bd = fields.Char(
        string = "URL BD"
        )
    edi_payslip_name_bd = fields.Char(
        string = "Nombre BD"
        )

    edi_payslip_user_pac = fields.Char(
        string="Usuario para PAC."
    )
    edi_payslip_pass_pac = fields.Char(
        string="Contraseña para PAC."
    )
    edi_payslip_test_pac = fields.Boolean(
        string="Modo de Prueba",
        default=False
    )
    edi_payslip_certificate_ids = fields.Many2many("einvoice.edi.certificate", readonly=False,
                                           string='Certificados MX')
    
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
        string="Fiscal Regime",
        help="It is used to fill Mexican XML CFDI"
        "Comprobante.Emisor.RegimenFiscal."
        )