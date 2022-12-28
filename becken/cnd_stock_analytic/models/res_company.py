# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    required_analytic_account_on_stock_move = fields.Boolean(
        string='Analytic account required',
        default=False,
        help="If marked, analytic account field is required in stock moves.")
    required_analytic_tags_on_stock_move = fields.Boolean(
        string='Analytic tags required',
        default=False,
        help="If marked, analytic tags field is required in stock moves.")
    required_analytic_account_on_stock_scrap = fields.Boolean(
        string='Analytic account required',
        default=False,
        help="If marked, analytic account field is required in scraps.")
    required_analytic_tags_on_stock_scrap = fields.Boolean(
        string='Analytic tags required',
        default=False,
        help="If marked, analytic tags field is required in scraps.")
