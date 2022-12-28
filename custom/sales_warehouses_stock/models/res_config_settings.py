# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_forecasted_stock_in_popup = fields.Boolean(
        string='Show forecasted stock in popup',
        related='company_id.show_forecasted_stock_in_popup',
        readonly=False,
        help="Show forecasted stock in popup in every sale order line.")
    show_available_stock_in_popup = fields.Boolean(
        string='Show available stock in popup',
        related='company_id.show_available_stock_in_popup',
        readonly=False,
        help="Show available stock in popup in every sale order line.")
