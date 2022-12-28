# -*- coding: utf-8 -*-group_sale_margin
from odoo import http, models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)


class WebsiteSaleDelivery(WebsiteSale):

    # Remover la línea del envío si el precio unitario es igual a CERO 0.00
    @http.route()
    def payment_transaction(self, *args, **kwargs):
        order = request.website.sale_get_order()
        free_delivery_lines = order.order_line.filtered(lambda a: a.price_unit == 0.00 and a.is_delivery == True)
        # free_delivery_lines = order.order_line.filtered(lambda a: a.price_unit == 0.00)
        if free_delivery_lines:
            free_delivery_lines.unlink()
        return super().payment_transaction(*args, **kwargs)
        
# Error al duplicar un pedido: Tipo de documento: Línea de la orden de venta (sale.order.line) Operación: read Ususario: 306 Campos: - purchase_price (permitido para grupos'Ver margen en Ventas')
# class SaleReport(models.Model):
#     _inherit = 'sale.report'

#     margin = fields.Float('Margin', groups="bck_crm_bant.group_sale_margin")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # margin = fields.Monetary(
    #     "Margin", compute='_compute_margin', store=True,
    #     groups="bck_crm_bant.group_sale_margin")
    # margin_percent = fields.Float(
    #     "Margin (%)", compute='_compute_margin', store=True,
    #     groups="bck_crm_bant.group_sale_margin")
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
            'EUR: Urgencia por error de UCIN\n',
    )
    ticket_number = fields.Char(string="Ticket", help="OSTicket number", copy=False)
    order_type_id = fields.Many2one(
        comodel_name="sale.order.type",
        string="Order Type",
        help="Select an Order Type",
    )
    route_id = fields.Many2one(
            'stock.location.route', string='Route', domain=[('sale_selectable', '=', True)], ondelete='restrict', check_company=True)

    # Validar que contenga Ticket antes de confirmar
    def action_confirm(self):
        for order in self:
            if not order.ticket_number:
                raise UserError(_(
                    'It is not allowed to confirm an order without "Ticket", sale order: %s'
                    ) % order.name)
            if not order.client_order_ref:
                raise UserError(_(
                    'It is not allowed to confirm an order without "Customer Reference", sale order: %s'
                    ) % order.name)
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            values = {'ticket_number': rec.ticket_number}
            if rec.shipping_mode:
                values.update({'shipping_mode': rec.shipping_mode})
            if rec.order_type_id:
                values.update({'order_type_id': rec.order_type_id.id})
            if rec.partner_id.commercial_partner_id.picking_warn != 'no-message' and rec.partner_id.commercial_partner_id.picking_warn_msg != False:
                values.update({'note': rec.partner_id.commercial_partner_id.picking_warn_msg})
            rec.picking_ids.write(values)
        return res
        
    @api.onchange('route_id')
    def onchange_route_id(self):
        for order_id in self:
            for line_id in order_id.order_line:
                line_id.route_id = order_id.route_id.id

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
            'shipping_mode': self.partner_id.commercial_partner_id.shipping_mode,
        }
        self.update(values)
        super(SaleOrder, self).onchange_partner_id()

    def action_quotation_send_without_mail(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=False).write({'state': 'sent'})
    
    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        vals = {
            'ticket_number': self.ticket_number,
        }
        invoice_vals.update(vals)

        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # margin = fields.Float(
    #     "Margin", compute='_compute_margin',
    #     digits='Product Price', store=True, groups="bck_crm_bant.group_sale_margin")
    # margin_percent = fields.Float(
    #     "Margin (%)", compute='_compute_margin', store=True, groups="bck_crm_bant.group_sale_margin", group_operator="avg")
    # purchase_price = fields.Float(
    #     string='Cost', compute="_compute_purchase_price",
    #     digits='Product Price', store=True, readonly=False,
    #     groups="bck_crm_bant.group_sale_margin")

    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        if self.order_id.route_id:
            self.route_id = self.order_id.route_id.id
        return result

    # @api.model
    # def create(self, vals):
    #     if 'route_id' not in vals:
    #         if self.order_id.route_id:
    #             vals['route_id'] =self.order_id.route_id.id
    #     return super().create(vals)

    # def write(self, values):
    #     if 'route_id' not in values:
    #         if self.order_id.route_id:
    #             values['route_id'] =self.order_id.route_id.id
    #     return super().write(values)
