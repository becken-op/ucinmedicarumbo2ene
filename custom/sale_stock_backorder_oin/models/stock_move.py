# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2021 Odoo IT now <http://www.odooitnow.com/>
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    def create_sol_backorder(self):
        self.ensure_one()
        context = dict(self._context) or {}
        picking_obj = self.env['stock.picking'].sudo()
        self.write({'product_uom_qty': context.get('product_uom_qty')})
        self._action_assign()

        # BACKORDER
        backorder = picking_obj.search([
            ('picking_type_id', '=', self.picking_id.picking_type_id.id),
            ('partner_id', '=', self.picking_id.partner_id.id),
            ('location_dest_id', '=', self.picking_id.location_dest_id.id),
            ('location_id', '=', self.picking_id.location_id.id),
            ('group_id', '=', self.picking_id.group_id.id),
            ('backorder_id', '=', self.picking_id.id)
        ])
        if not backorder:
            backorder = self.env['stock.picking'].sudo().create({
                'picking_type_id': self.picking_id.picking_type_id.id,
                'partner_id': self.picking_id.partner_id.id,
                'date': self.picking_id.date,
                'origin': self.picking_id.origin,
                'location_dest_id': self.picking_id.location_dest_id.id,
                'location_id': self.picking_id.location_id.id,
                'company_id': self.picking_id.company_id.id,
                'group_id': self.picking_id.group_id.id,
                'backorder_id': self.picking_id.id,
            })

        # BACKORDER LINES
        move_values = self.sale_line_id.with_context(
            {'product_uom_qty': context.get('product_uom_qty'),
             'product_id': context.get('product_id'),
             'group_id': self.picking_id.group_id.id})._prepare_stock_moves(
                 backorder)
        self.sudo().create(move_values)

        return backorder
