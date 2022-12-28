# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    customer_product_manager_id = fields.Many2one('res.users', string='Product Manager',
        help='The internal user in charge of this products contact.')

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ",partner.product_manager_id as customer_product_manager_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ",partner.product_manager_id"
