# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    shipping_mode = fields.Selection([
        ('rel', 'REL'),
        ('rho', 'RHO'),
        ('rdi', 'RDI'),
        ('pco', 'PCO'),
        ('ppa', 'PPA'),
        ('eav', 'EAV'),
        ('epr', 'EPR'),
        ('eur', 'EUR'),],
        string='Shipping mode',
        help='REL: Recolección\n'
            'RHO: Ruta UCIN Hospitales\n'
            'RDI: Ruta UCIN Distribuidores\n'
            'PCO: Paqueteria con cobro\n'
            'PPA: Paqueteria pagada por UCIN\n'
            'EAV: Entrega Asesor de Ventas asignado\n'
            'EPR: Entrega programada\n'
            'EUR: Urgencia por error de UCIN\n'
    )
    ticket_number = fields.Char(string="Ticket", help="OSTicket number")
    order_type_id = fields.Many2one(
        comodel_name="sale.order.type",
        string="Order Type",
        help="Select an Order Type",
    )

    # Validar que contenga Ticket antes de confirmar
    def _action_done(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                if not picking.immediate_transfer:
                    for move_line_id in picking.move_line_ids_without_package:
                        if move_line_id.qty_done > move_line_id.product_uom_qty:
                            raise UserError(_(
                                'It is not allowed to move or delivery more than demand quantity, product: %s'
                                ) % move_line_id.product_id.name)

                if not picking.ticket_number:
                    raise UserError(_(
                        'It is not allowed to confirm a delivery without ticket, delivery: %s'
                        ) % picking.name)
                if picking.shipping_mode in ('ppa', 'pco') and (not picking.carrier_id or not picking.carrier_tracking_ref):
                    raise UserError(_(
                        'It is not allowed to confirm a delivery without Carrier and Tracking Reference with Shipping mode PCO or PPA, delivery: %s'
                        ) % picking.name)

                # Candado para entregar al cliente si no ha pagado y su tipo de pago es Inmediato
                sale_order_ids = picking.move_lines.sale_line_id.order_id
                sale_amount_total = 0.0
                for sale_order_id in sale_order_ids:
                    sale_amount_total += sale_order_id.amount_total

                paid_invoice_ids = picking.move_lines.sale_line_id.invoice_lines.move_id.filtered(
                    lambda x: x.move_type == 'out_invoice' and x.payment_state in ('paid', 'in_payment'))
                immediate_payment = self.env.ref('account.account_payment_term_immediate', raise_if_not_found=False)

                if not paid_invoice_ids and sale_order_ids.payment_term_id == immediate_payment:
                    if picking.partner_id.commercial_partner_id.property_payment_term_id == immediate_payment:
                        raise UserError(_('This customer has Immediate Payment Term and its Sale Order has not been paid.'))
                elif  sale_order_ids.payment_term_id == immediate_payment:
                    amount_total = 0.0
                    for paid_invoice_id in paid_invoice_ids:
                        if paid_invoice_id.invoice_payment_term_id == immediate_payment:
                            amount_total += paid_invoice_id.amount_total
                    if amount_total < sale_amount_total:
                        raise UserError(_('The total amount of its Sale Order has not been paid.'))

        super(Picking, self)._action_done()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - shipping_mode
        """
        if not self.partner_id:
            self.update({
                'shipping_mode': False,
            })
            return
        values = {
            'shipping_mode': self.partner_id.shipping_mode,
        }
        self.update(values)
        super(Picking, self).onchange_partner_id()
