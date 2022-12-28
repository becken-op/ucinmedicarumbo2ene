# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_sale_orders = fields.Boolean(
        string='Restrict Sale Orders',
        related='company_id.restrict_sale_orders',
        readonly=False,
        help="If marked, restrict confirm Sale Orders if the customer has exceeded the credit limit.")

    restrict_invoices = fields.Boolean(
        string='Restrict Customer Invoices',
        related='company_id.restrict_invoices',
        readonly=False,
        help="If marked, restrict confirm customer invoices if the customer has exceeded the credit limit.")

    restrict_transfers = fields.Boolean(
        string='Restrict Stock Transfers',
        related='company_id.restrict_transfers',
        readonly=False,
        help="If marked, restrict validate stock transfers if the customer has exceeded the credit limit.")

    restrict_sales_by_due_invoices = fields.Boolean(
        string='Restrict Sales by Due Invoices',
        related='company_id.restrict_sales_by_due_invoices',
        readonly=False,
        help='If marked, restrict confirm Sale Orders if the customer if has Due Invoices with more days than customer extra days, without considering the customer\'s credit limit.',
    )
