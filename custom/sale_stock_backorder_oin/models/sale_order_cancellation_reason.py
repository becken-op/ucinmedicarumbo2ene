# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderCancellationReason(models.Model):
    _name = 'sale.order.cancellation.reason'
    _description = 'Sale Order Cancellation Reason'

    name = fields.Char(string="Cancellation Reason", required=True, copy=False)
