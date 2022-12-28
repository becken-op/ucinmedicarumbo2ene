# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderType(models.Model):
    _name = 'sale.order.type'
    _description = 'Sale Order Type'

    name = fields.Char(string="Sale Order Type", required=True, copy=False)
