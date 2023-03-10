# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta
from collections import defaultdict
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # qty_per_warehouse_ids = fields.One2many('warehouse.stock.qty', 'sale_order_line_id', readonly=True)
    # qty_per_warehouse_ids = fields.One2many(
    #     comodel_name='warehouse.stock.qty', inverse_name='sale_order_line_id',
    #     string='Qty per Warehouse', readonly=True)
    qty_per_warehouse_ids_text = fields.Text(compute='_compute_qty_at_date')

    @api.depends(
        'product_id', 'customer_lead', 'product_uom_qty', 'product_uom', 'order_id.commitment_date',
        'move_ids', 'move_ids.forecast_expected_date', 'move_ids.forecast_availability')
    def _compute_qty_at_date(self):
        """ Compute the quantity forecasted of product at delivery date. There are
        two cases:
            1. The quotation has a commitment_date, we take it as delivery date
            2. The quotation hasn't commitment_date, we compute the estimated delivery
                date based on lead time"""
        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
        # If the state is already in sale the picking is created and a simple forecasted quantity isn't enough
        # Then used the forecasted data of the related stock.move
        warehouse_ids = []
        for line in self:
            if not line.display_qty_widget: #or line.qty_per_warehouse_ids:
                continue
            moves = line.move_ids.filtered(lambda m: m.product_id == line.product_id)

            # JCT
            # line.qty_per_warehouse_ids = False
            # line.qty_per_warehouse_ids_text = False
            line.warehouse_id = line.order_id.warehouse_id

            line.forecast_expected_date = max(moves.filtered("forecast_expected_date").mapped("forecast_expected_date"), default=False)
            line.qty_available_today = 0
            line.free_qty_today = 0
            for move in moves:
                line.qty_available_today += move.product_uom._compute_quantity(move.reserved_availability, line.product_uom)
                line.free_qty_today += move.product_id.uom_id._compute_quantity(move.forecast_availability, line.product_uom)
            line.scheduled_date = line.order_id.commitment_date or line._expected_date()
            line.virtual_available_at_date = False
            # treated |= line

            # JCT
            warehouse_ids = line.warehouse_id
            warehouse_ids += self.env['stock.warehouse'].search([('company_id', '=', line.order_id.company_id.id), ('id', '!=', line.warehouse_id.id)])
            for warehouse_id in warehouse_ids:
                if line.order_id.commitment_date:
                    date = line.order_id.commitment_date
                else:
                    confirm_date = line.order_id.date_order if line.order_id.state in ['sale', 'done'] else datetime.now()
                    date = confirm_date + timedelta(days=line.customer_lead or 0.0)
                grouped_lines[(warehouse_id.id, warehouse_id.display_name, date)] |= line

        # We first loop over the SO lines to group them by warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        # for line in self.filtered(lambda l: l.state in ('draft', 'sent')):
        #     if not (line.product_id and line.display_qty_widget):
        #         continue
        #     grouped_lines[(line.warehouse_id.id, line.order_id.commitment_date or line._expected_date())] |= line
        treated = self.browse()
        qty_per_warehouse_ids = []
        for (warehouse, warehouse_name, scheduled_date), lines in grouped_lines.items():
            product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            qties_per_product = {
                (product['id'], warehouse): (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                values = {}
                if line.warehouse_id.id == warehouse:
                    line.scheduled_date = scheduled_date
                    qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id, warehouse]
                    line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id, warehouse]
                    line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id, warehouse]
                    line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[line.product_id.id, warehouse]
                    line.forecast_expected_date = False
                    product_qty = line.product_uom_qty
                    if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
                        line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today, line.product_uom)
                        line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today, line.product_uom)
                        line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(line.virtual_available_at_date, line.product_uom)
                        product_qty = line.product_uom._compute_quantity(product_qty, line.product_id.uom_id)
                    qty_processed_per_product[line.product_id.id, warehouse] += product_qty

                    values = {
                        'warehouse_id': warehouse,
                        'warehouse_name': warehouse_name,
                        'qty_available': line.qty_available_today,
                        'free_qty': line.free_qty_today,
                        'virtual_available': line.virtual_available_at_date,
                        'product_id': line.product_id.id
                    }
                else:
                    qty_available_today_var, free_qty_today_var, virtual_available_at_date_var = qties_per_product[(line.product_id.id, warehouse)]
                    qty_available_today = qty_available_today_var - qty_processed_per_product[(line.product_id.id, warehouse)]
                    free_qty_today = free_qty_today_var - qty_processed_per_product[(line.product_id.id, warehouse)]
                    virtual_available_at_date = virtual_available_at_date_var - qty_processed_per_product[(line.product_id.id, warehouse)]
                    qty_processed_per_product[(line.product_id.id, warehouse)] += line.product_uom_qty
                    values = {
                        'warehouse_id': warehouse,
                        'warehouse_name': warehouse_name,
                        'qty_available': qty_available_today,
                        'free_qty': free_qty_today,
                        'virtual_available': virtual_available_at_date,
                        'product_id': line.product_id.id
                    }
                qty_per_warehouse_ids.append(values)


            treated |= lines
        self.qty_per_warehouse_ids_text = json.dumps(qty_per_warehouse_ids)

        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.forecast_expected_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False
        remaining.warehouse_id = False
        remaining.qty_per_warehouse_ids_text = False

