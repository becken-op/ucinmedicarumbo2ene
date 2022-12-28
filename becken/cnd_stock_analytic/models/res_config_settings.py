# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    required_analytic_account_on_stock_move = fields.Boolean(
        string='Analytic account required',
        related='company_id.required_analytic_account_on_stock_move',
        readonly=False,
        help="If marked, analytic account field is required in stock moves.")
    required_analytic_tags_on_stock_move = fields.Boolean(
        string='Analytic tags required',
        related='company_id.required_analytic_tags_on_stock_move',
        readonly=False,
        help="If marked, analytic tags field is required in stock moves.")
    required_analytic_account_on_stock_scrap = fields.Boolean(
        string='Analytic account required',
        related='company_id.required_analytic_account_on_stock_scrap',
        readonly=False,
        help="If marked, analytic account field is required in scraps.")
    required_analytic_tags_on_stock_scrap = fields.Boolean(
        string='Analytic tags required',
        related='company_id.required_analytic_tags_on_stock_scrap',
        readonly=False,
        help="If marked, analytic tags field is required in scraps.")
