# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_inventory_user_validation_max_amount = fields.Monetary(
        string='User Validation Max. Amount',
        currency_field='currency_id',
        default=0.00,
        help="Maximum cost amount of Inventory Adjustment that can be validated by an Inventory User, more than this amount need to be validated by Stock Manager.")
