# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    supplier_xml_amount_margin = fields.Monetary(string="Margen de comparacion de monto",default=0)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    supplier_xml_amount_margin = fields.Monetary(related='company_id.supplier_xml_amount_margin',
    	string="Margen de comparacion de monto", currency_field='company_currency_id',readonly=False)