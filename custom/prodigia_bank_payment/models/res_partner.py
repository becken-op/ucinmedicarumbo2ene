# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_id_key = fields.Char(string='Supplier ID Key',
        help='Supplier ID Key to generate portal bank payment files. This field must be 13 characters long.')
