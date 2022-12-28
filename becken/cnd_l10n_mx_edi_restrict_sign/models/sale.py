# -*- coding: utf-8 -*-
from odoo import fields, api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        self.ensure_one()

        invoice_vals = super(SaleOrder, self)._prepare_invoice()

        vals = {
            'l10n_mx_edi_sign_required': self.partner_id.commercial_partner_id.l10n_mx_edi_sign_required,
            'l10n_mx_edi_payment_sign_required': self.partner_id.commercial_partner_id.l10n_mx_edi_sign_required,
        }
        invoice_vals.update(vals)

        return invoice_vals
