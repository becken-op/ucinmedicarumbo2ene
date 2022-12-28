# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang


class AccountMove(models.Model):
    _inherit = "account.move"

    allow_exceeding_credit_limit = fields.Boolean(
        string='Allow Exceeding Credit Limit?',
        tracking=True,
        related='partner_id.commercial_partner_id.allow_override',
        store=True,
        help='Allow invoice with customer credit limit overrode',
        default=False)
    credit_extra_days = fields.Integer(
        string='Extra Days',
        related='partner_id.credit_extra_days',
        help='Block Invoicing to this customer if has Due Invoices with more days than customer extra days.',
    )

    def action_post(self):
        for invoice in self:
            immediate_payment = invoice.env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
            if invoice.partner_id:
                if (not invoice.invoice_payment_term_id or invoice.invoice_payment_term_id.id != immediate_payment.id) \
                and invoice.company_id.restrict_invoices \
                and invoice.move_type == 'out_invoice':
                    if not invoice.allow_exceeding_credit_limit and not invoice.partner_id.commercial_partner_id.allow_override:
                        company_currency_id = invoice.company_id.currency_id
                        current_invoice_amount = invoice.amount_total_signed
                        # balance = invoice.partner_id.commercial_partner_id.balance
                        credit_limit = invoice.partner_id.commercial_partner_id.credit_limit
                        available_credit_amount = invoice.partner_id.commercial_partner_id.available_credit_amount
                        credit = invoice.partner_id.commercial_partner_id.credit

                        # Si el cliente tiene límite de crédito mayor a 0
                        if available_credit_amount - current_invoice_amount < 0:
                            raise ValidationError(
                                _("Credit limit exceeded by this customer. Please, contact to your "
                                "\"Credit & Collection Department\".\n"
                                "\n    Credit Limit: %s"
                                "\n    Credit: %s"
                                "\n    Available Credit: %s")
                                % (formatLang(invoice.env, credit_limit, currency_obj=company_currency_id),
                                formatLang(invoice.env, credit, currency_obj=company_currency_id),
                                formatLang(invoice.env, available_credit_amount, currency_obj=company_currency_id)))
        return super(AccountMove, self).action_post()
