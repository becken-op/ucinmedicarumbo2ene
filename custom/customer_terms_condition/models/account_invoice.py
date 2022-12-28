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


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def _default_comment(self):
        invoice_type = self.env.context.get('type', 'out_invoice')
        if invoice_type == 'out_invoice' and self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms'):
            return ''
    
    narration = fields.Text(string='Internal Note',default=_default_comment)
   
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        # Customer Comment In Sale Order
        if self.partner_id.commercial_partner_id.invoice_terms:
            self.narration = self.partner_id.commercial_partner_id.invoice_terms 
        elif self.env.user.company_id.invoice_terms:
            self.narration = self.env.user.company_id.invoice_terms
        else:
            self.narration = ''
        return res

    @api.onchange('partner_id', 'company_id')
    def _onchange_delivery_address(self):
        addr = self.partner_id.address_get(['delivery'])
        self.partner_shipping_id = addr and addr.get('delivery')
        if self.env.context.get('type', 'out_invoice') == 'out_invoice':
            company = self.company_id or self.env.user.company_id
            # Customer Comment Set in account invoice
            if self.partner_id.commercial_partner_id.invoice_terms:
                self.narration = self.partner_id.commercial_partner_id.invoice_terms
            elif self.env.user.company_id.invoice_terms:
                self.narration = self.env.user.company_id.invoice_terms
            else:
                self.narration = ''

