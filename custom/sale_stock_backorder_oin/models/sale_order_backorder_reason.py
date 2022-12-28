# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderBackorderReason(models.Model):
    _name = 'sale.order.backorder.reason'
    _description = 'Sale Order Backorder Reason'

    name = fields.Char(string="Backorder Reason", required=True, copy=False)
