# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    credit_limit = fields.Monetary(
        string='Credit Limit',
        tracking=True)
    allow_override = fields.Boolean(
        string='Allow Override',
        default=False,
        tracking=True,
        help="Allow override credit limit, if marked, you can confirm sales to this customer.")
    available_credit_amount = fields.Monetary(
        'Credit Available', store=True, compute='_compute_amount_credit_available')
    balance = fields.Monetary(
        string='Balance', store=True,
        compute='_compute_amount_credit_available',
        help="Technical field holding the debit - credit in order to open meaningful graph views from reports")
    has_credit = fields.Boolean(
        string='Has Credit',
        store=True,
        compute='_compute_has_credit',
        help="A customer has credit if their Payment Term is different to Innmediate Payment.")
    credit_extra_days = fields.Integer(
        string='Extra Days',
        default=0,
        help='Block Invoicing to this customer if has Due Invoices with more days than customer extra days.',
    )

    @api.depends('property_payment_term_id')
    def _compute_has_credit(self):
        immediate_payment = self.env.ref(
            'account.account_payment_term_immediate')
        for partner in self:
            if partner.property_payment_term_id and partner.property_payment_term_id != immediate_payment:
                partner.has_credit = True
            else:
                partner.has_credit = False

    @api.depends('credit_limit', 'credit', 'debit')
    def _compute_amount_credit_available(self):
        for partner in self:
            partner.available_credit_amount = partner.credit_limit - \
                partner.credit + partner.debit
            partner.balance = partner.debit - partner.credit
