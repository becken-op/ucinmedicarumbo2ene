# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    l10n_mx_edi_sign_required = fields.Boolean(
        string='Sign CFDI?',
        help='If this field is active, the CFDI will be generated for this invoice.')

    def _select(self):
        select = ",move.l10n_mx_edi_sign_required"

        return super(AccountInvoiceReport, self)._select() + select

    def _group_by(self):
        group = ",move.l10n_mx_edi_sign_required"
        return super(AccountInvoiceReport, self)._group_by() + group
