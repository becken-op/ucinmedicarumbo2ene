# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang


class CreditLimitStockPicking(models.Model):
    _name = "stock.picking"
    _inherit = 'stock.picking'

    allow_exceeding_credit_limit = fields.Boolean(
        string='Allow Exceeding Credit Limit?',
        tracking=True,
        related='partner_id.commercial_partner_id.allow_override',
        store=True,
        help='Allow delivery with customer credit limit overrode',
        default=False)

    def button_validate(self):
        self.ensure_one()

        # Si la transferencia es una entrega a cliente
        if self.picking_type_code == 'outgoing':
            immediate_payment = self.env.ref('account.account_payment_term_immediate')

            if (not self.sale_id.payment_term_id or self.sale_id.payment_term_id.id != immediate_payment.id) \
               and self.company_id.restrict_transfers:
                if not self.allow_exceeding_credit_limit and not self.partner_id.commercial_partner_id.allow_override:
                    company_currency_id = self.company_id.currency_id
                    # balance = self.partner_id.commercial_partner_id.balance
                    credit_limit = self.partner_id.commercial_partner_id.credit_limit
                    available_credit_amount = self.partner_id.commercial_partner_id.available_credit_amount
                    credit = self.partner_id.commercial_partner_id.credit

                    # Si tengo límite de crédito mayor a 0
                    if available_credit_amount < 0:
                        raise ValidationError(
                            _("Credit limit exceeded by this customer. Please, contact to your "
                              "\"Credit & Collection Department\".\n"
                              "\n    Credit Limit: %s"
                              "\n    Credit: %s"
                              "\n    Available Credit: %s")
                            % (formatLang(self.env, credit_limit, currency_obj=company_currency_id),
                               formatLang(self.env, credit, currency_obj=company_currency_id),
                               formatLang(self.env, available_credit_amount, currency_obj=company_currency_id)))

        res = super(CreditLimitStockPicking, self).button_validate()
        return res
