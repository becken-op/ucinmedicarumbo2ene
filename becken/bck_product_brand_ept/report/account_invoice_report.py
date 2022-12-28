# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    product_brand_ept_id = fields.Many2one(
        'product.brand.ept',
        string='Product Brand',
        help='Select a brand for this product',
        readonly=True,
    )

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ",template.product_brand_ept_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ",template.product_brand_ept_id"
