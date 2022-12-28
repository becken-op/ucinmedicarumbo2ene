# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stock_inventory_user_validation_max_amount = fields.Monetary(
        string='User Validation Max. Amount',
        currency_field='currency_id',
        related='company_id.stock_inventory_user_validation_max_amount',
        readonly=False,
        help="Maximum cost amount of Inventory Adjustment that can be validated by any Inventory User, more than this amount need to be validated by Stock Manager.")
