# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    required_analytic_account_on_stock_inventory = fields.Boolean(
        string='Analytic account required',
        default=False,
        help="If marked, analytic account field is required in inventory adjusments.")
    required_analytic_tags_on_stock_inventory = fields.Boolean(
        string='Analytic tags required',
        default=False,
        help="If marked, analytic tags field is required in inventory adjusments.")
