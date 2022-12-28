# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    customer_tradename = fields.Char(string="Customer Tradename", readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ",partner.tradename as customer_tradename"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ",partner.tradename"
