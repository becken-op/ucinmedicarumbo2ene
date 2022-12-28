#-*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    show_button_refresh = fields.Boolean(default=True)

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
            order._refresh_seller_price_value()
        return True

    def _refresh_seller_price_value(self):
        for line in self.order_line:
            price = line.price_unit
            product = line.product_id
            seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)
            if price != seller.price:
                seller.write({'price':price})    
                product._compute_most_cost_price()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
   
   
    def _refresh_seller_price_value(self):
        for line in self:
            price = line.price_unit
            product = line.product_id
            seller = line.product_id._select_seller(
                    partner_id=line.partner_id)
            if price != seller.price:
                seller.write({'price':price})    
                product._compute_most_cost_price()

    
    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_('You cannot change the type of a purchase order line. Instead you should delete the current line and create a new line of the proper type.'))

        if 'product_qty' in values:
            for line in self:
                if line.order_id.state == 'purchase':
                    line.order_id.message_post_with_view('purchase.track_po_line_template',
                                                         values={'line': line, 'product_qty': values['product_qty']},
                                                         subtype_id=self.env.ref('mail.mt_note').id)
        if 'qty_received' in values:
            for line in self:
                line._track_qty_received(values['qty_received'])
        res = super(PurchaseOrderLine, self).write(values)
        for order in self:
            order._refresh_seller_price_value()
        return res