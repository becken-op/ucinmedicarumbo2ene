# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    customer_product_manager_id = fields.Many2one('res.users', string='Product Manager',
        help='The internal user in charge of this products contact.')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['customer_state'] = ", partner.product_manager_id AS customer_product_manager_id"
        groupby += ', partner.product_manager_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
