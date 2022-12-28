# -*- coding: utf-8 -*-

from odoo import models, fields


class WarehouseStockQty(models.Model):
    _name = 'warehouse.stock.qty'
    _description = 'Warehouse stock qty'
    _rec_name = 'warehouse_id'

    sale_order_line_id = fields.Many2one('sale.order.line')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True)
    qty_available = fields.Float(required=True)
    free_qty = fields.Float(required=True)
    virtual_available = fields.Float(required=True)
    show_forecasted_stock_in_popup = fields.Boolean(
        string='Show forecasted stock in popup',
        related='sale_order_line_id.company_id.show_forecasted_stock_in_popup',
        help="Show forecasted stock in popup in every sale order line.")
    show_available_stock_in_popup = fields.Boolean(
        string='Show available stock in popup',
        related='sale_order_line_id.company_id.show_available_stock_in_popup',
        help="Show available stock in popup in every sale order line.")