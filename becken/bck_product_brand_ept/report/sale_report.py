# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    product_brand_ept_id = fields.Many2one(
        'product.brand.ept',
        string='Product Brand',
        help='Select a brand for this product',
        readonly=True,
    )

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['product_brand_ept_id'] = ", t.product_brand_ept_id"
        groupby += ', t.product_brand_ept_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
