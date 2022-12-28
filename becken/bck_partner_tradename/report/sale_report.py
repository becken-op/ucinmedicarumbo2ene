# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    customer_tradename = fields.Char(string="Customer Tradename", readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['customer_tradename'] = ", partner.tradename AS customer_tradename"
        groupby += ', partner.tradename'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
