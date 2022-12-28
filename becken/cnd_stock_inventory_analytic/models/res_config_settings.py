# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    required_analytic_account_on_stock_inventory = fields.Boolean(
        string='Analytic account required',
        related='company_id.required_analytic_account_on_stock_inventory',
        readonly=False,
        help="If marked, analytic account field is required in inventory adjusments.")
    required_analytic_tags_on_stock_inventory = fields.Boolean(
        string='Analytic tags required',
        related='company_id.required_analytic_tags_on_stock_inventory',
        readonly=False,
        help="If marked, analytic tags field is required in inventory adjusments.")
    