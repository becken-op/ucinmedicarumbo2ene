# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_forecasted_stock_in_popup = fields.Boolean(
        string='Show forecasted stock in popup',
        default=True,
        help="Show forecasted stock in popup in every sale order line.")
    show_available_stock_in_popup = fields.Boolean(
        string='Show available stock in popup',
        default=True,
        help="Show available stock in popup in every sale order line.")
