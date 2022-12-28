# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    ticket_number = fields.Char(string="Ticket", help="OSTicket number")
    collection_state = fields.Selection([
        ('OC en trámite', 'OC en trámite'),
        ('Firma/Sello', 'Firma/Sello'),
        ('En aclaración', 'En aclaración'),
        ('Ok', 'Ok')],
        string="Estado de Cobranza",
        tracking=True,
        help="")

    # Validar que contenga Ticket antes de confirmar
    def action_post(self):
        for invoice in self:
            if not invoice.ticket_number and invoice.move_type=='out_invoice':
                raise UserError(_(
                    'It is not allowed to confirm an invoice without ticket, invoice: %s'
                    ) % invoice.id)
        super(AccountMove, self).action_post()
