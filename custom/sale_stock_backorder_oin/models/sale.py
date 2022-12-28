# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2021 Odoo IT now <http://www.odooitnow.com/>
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_order_cancellation_reason_id = fields.Many2one(
        comodel_name="sale.order.cancellation.reason",
        string="Cancellation Reason",
        help="Select a Cancellation Reason",
    )
    has_line_cancelled = fields.Boolean(
        string="Has line cancelled",
        compute='compute_has_line_cancelled',
        copy=False,
        help="Has any line cancelled",
    )
    sale_order_backorder_reason_id = fields.Many2one(
        comodel_name="sale.order.backorder.reason",
        string="Backorder Reason",
        copy=False,
        help="Select a Backorder Reason",
    )
    has_line_backorder = fields.Boolean(
        string="Has line backorder",
        compute='compute_has_line_backorder',
        help="Has any line cancelled",
    )

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        order_id = super(SaleOrder, self).copy(default)
        for line in order_id.order_line:
            line.compute_available_qty()
        return order_id

    @api.onchange('order_line.qty_cancelled')
    @api.depends('order_line.qty_cancelled')
    def compute_has_line_cancelled(self):
        for order_id in self:
            # qty_cancelled_total = order_id.order_line.read_group(
            #     domain=[], fields=['qty_cancelled:sum'],
            #     groupby=[], lazy=False)
            # qty_cancelled = qty_cancelled_total[0]['qty_cancelled']
            # prunt('qty_cancelled: ', qty_cancelled)
            qty_cancelled = 0.00
            for line in order_id.order_line:
                qty_cancelled += line.qty_cancelled
            if qty_cancelled != 0.00:
                order_id.has_line_cancelled = True
            else:
                order_id.has_line_cancelled = False

    @api.onchange('order_line.qty_backorder')
    @api.depends('order_line.qty_backorder')
    def compute_has_line_backorder(self):
        for order_id in self:
            qty_backorder = 0.00
            for line in order_id.order_line:
                qty_backorder += line.qty_backorder
            if qty_backorder != 0.00:
                order_id.has_line_backorder = True
            else:
                order_id.has_line_backorder = False

    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     moves_obj = self.env['stock.move'].sudo()
    #     for line in self.order_line.filtered(lambda l: l.qty_backorder):
    #         moves = moves_obj.search([('sale_line_id', '=', line.id)])
    #         for move in moves:
    #             move.with_context(
    #                 product_uom_qty=line.product_uom_qty - line.qty_backorder,
    #                 product_id=move.product_id.id).create_sol_backorder()
    #     return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        moves_obj = self.env['stock.move'].sudo()
        for line in self.order_line.filtered(lambda l: l.qty_backorder):
            # moves = moves_obj.search([('sale_line_id', '=', line.id)])
            moves = line.move_ids
            for move in moves:
                _logger.info('Backorder: ' + str(line.qty_backorder))
                product_uom_qty = line.product_uom_qty - line.qty_backorder
                _logger.info('Line: %s, Qty: %s' % (line.name, str(line.product_uom_qty)))
                move.with_context(
                    product_uom_qty=product_uom_qty,
                    product_id=move.product_id.id).create_sol_backorder()
                # move.write({'product_uom_qty': product_uom_qty})
                # _logger.info('Line: %s, Qty: %s' % (line.name, str(line.product_uom_qty)))
                if product_uom_qty == 0.00:
                    move._action_cancel()
                    # move.unlink()
                    # move.picking_id.move_ids_without_package = (3, move.id)
        return res
    
    # def _force_lines_to_invoice_policy_order(self):
    #     for line in self.order_line:
    #         if self.state in ['sale', 'done']:
    #             # Buscar si tiene movimientos "Listos" a la ubicación "Partner Locations/Customers",
    #             # para que se facture solamente lo reservado en la última operación.
    #             # line.move_ids.picking_id
    #             line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
    #         else:
    #             line.qty_to_invoice = 0


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float(compute='compute_available_qty',
                                 compute_sudo=True,
                                 string='Available Qty.',
                                 store=True,
                                 default=0.00)
    qty_backorder = fields.Float(string='BackOrder Qty.',
                                 compute='compute_available_qty',
                                 compute_sudo=True,
                                 store=True,
                                 default=0.00)
    qty_cancelled = fields.Float(string='Cancelled Qty.',
                                default=0.00)
    qty_prevoius_cancelled = fields.Float(string='Prevoius Cancelled Qty.',
                                default=0.00)
            
    @api.onchange('qty_cancelled')
    def onchange_qty_cancelled(self):
        for line in self:
            if line.product_uom_qty + line.qty_prevoius_cancelled - line.qty_cancelled >= 0.00:
                line.product_uom_qty = line.product_uom_qty + line.qty_prevoius_cancelled - line.qty_cancelled
            else:
                line.product_uom_qty = 0
                line.qty_cancelled = line.product_uom_qty + line.qty_prevoius_cancelled
            line.qty_prevoius_cancelled = line.qty_cancelled

    @api.onchange('product_id', 'product_uom_qty')
    def compute_available_qty(self):
        for line in self:
            if not line.product_id:
                return
            
            product_qties = line.product_id.with_context(to_date=fields.Datetime.now(), warehouse=line.order_id.warehouse_id.id).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            line.qty_available = product_qties[0]['free_qty']
            # Original: line.qty_available = line.product_id.qty_available
            if line.product_uom_qty > line.qty_available:
                line.qty_backorder = line.product_uom_qty - line.qty_available
            else:
                line.qty_backorder = 0.00


    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function
        returns a list of dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        context = dict(self._context) or {}
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        
        date_deadline = self.order_id.commitment_date or (self.order_id.date_order + timedelta(days=self.customer_lead or 0.0))
        date_planned = date_deadline - timedelta(days=self.order_id.company_id.security_lead)

        template = {
            'name': self.name or '',
            'product_id': context.get('product_id'),
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.partner_id.property_stock_customer.id,
            'picking_id': picking.id,
            'partner_id': picking.partner_id.id,
            'state': 'waiting',
            'company_id': picking.company_id.id,
            'price_unit': self.price_unit or 0.0,
            'picking_type_id': picking.picking_type_id.id,
            'group_id': context.get('group_id'),
            'origin': picking.name,
            'route_ids': [(6, 0, picking.picking_type_id.warehouse_id.route_ids.ids)] or [],
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
            'sale_line_id': self.id,
            'date': date_planned,
            'date_deadline': date_deadline,
        }

        if float_compare(self.qty_backorder, 0.0,
                         precision_rounding=self.product_uom.rounding) > 0:
            product_id = self.env['product.product'].browse(
                context.get('product_id'))
            template['product_uom_qty'] = self.qty_backorder
        res.append(template)
        return res
    
    # # no trigger product_id.invoice_policy to avoid retroactively changing SO
    # @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    # def _get_to_invoice_qty(self):
    #     """
    #     Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
    #     calculated from the ordered quantity. Otherwise, the quantity delivered is used.
    #     """
    #     for line in self:
    #         if line.order_id.state in ['sale', 'done']:
    #             if line.product_id.invoice_policy == 'order':
    #                 line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
    #             else:
    #                 line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
    #         else:
    #             line.qty_to_invoice = 0


    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        customer_location = self.env.ref('stock.stock_location_customers')
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    # Buscar si tiene movimientos "Listos" a la ubicación "Partner Locations/Customers",
                    # para que se facture solamente lo reservado en la última operación.
                    assigned_move_ids = line.move_ids.filtered(lambda m: m.state in ['assigned', 'done'] and m.location_dest_id.id == customer_location.id)
                    forecast_availability = 0
                    for move_id in assigned_move_ids:
                        if move_id.state == 'assigned':
                            forecast_availability += move_id.forecast_availability
                        elif move_id.state == 'done':
                            # forecast_availability += move_id.quantity_done
                            forecast_availability = line.qty_delivered - line.qty_invoiced
                            break
                    # Original
                    # line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                    qty_to_invoice = forecast_availability - line.qty_invoiced
                    if qty_to_invoice < 0.00:
                        qty_to_invoice = 0.00
                    line.qty_to_invoice = qty_to_invoice
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    # TODO: Cuando todo el pedido es backorder nunca generará factura, y cuando regresa {} si genera la línea pero sin producto
    # def _prepare_invoice_line(self, **optional_values):   
    #     res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
    #     if not self.order_id.invoice_count:
    #         qty_to_invoice = self.qty_to_invoice - self.qty_backorder
    #         if qty_to_invoice <= 0:
    #             return {}
    #         else:
    #             res.update({'quantity': qty_to_invoice})
    #     return res
