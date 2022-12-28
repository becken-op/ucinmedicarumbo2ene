# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_note(self):
        return ''

    note = fields.Text('Terms and conditions', default=_default_note)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'user_id': self.partner_id.user_id.id or self.env.uid
        }
        # Customer Terms And Condition Added In Sale Order
        if self.partner_id.commercial_partner_id.invoice_terms:
            values['note'] = self.partner_id.commercial_partner_id.invoice_terms 
        elif self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.user.company_id.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.invoice_terms
        else:
            values['note'] = ''

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)