# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Odoo S.A. <http://www.odoo.com>
#    @author Paramjit Singh A. Sahota <sahotaparamjitsingh@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'l10n_mx_edi.pac.sw.mixin']

    def l10n_mx_edi_is_required(self):
        self.ensure_one()
        required = (
            self.reconciled_invoice_ids.filtered(lambda i: i.l10n_mx_edi_payment_sign_required is False))
        if required:
            return not required
        required = super(AccountPayment, self).l10n_mx_edi_is_required()
        return required
