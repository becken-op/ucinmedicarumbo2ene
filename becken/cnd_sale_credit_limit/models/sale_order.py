# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class CreditLimitAlertSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    allow_exceeding_credit_limit = fields.Boolean(
        string='Allow Exceeding Credit Limit?',
        related='partner_id.commercial_partner_id.allow_override',
        store=True,
        tracking=True,
        default=False)

    def action_confirm(self):
        # Término de pago inmediato
        immediate_payment = self.env.ref('account.account_payment_term_immediate')

        # Verificar si es un pedido web
        # Si no tiene payment.transaction, verificar el límite de crédito, si el pedido viene del ecommerce,
        # no restringir
        restrict_sale_orders = self.company_id.restrict_sale_orders
        restrict_sales_by_due_invoices = self.company_id.restrict_sales_by_due_invoices
        # _logger.info((not self.payment_term_id or self.payment_term_id.id != immediate_payment.id))
        # _logger.info((restrict_sale_orders or restrict_sales_by_due_invoices))
        # _logger.info(not ('website_id' in self and self.website_id is False))
        if (not self.payment_term_id or self.payment_term_id.id != immediate_payment.id) \
            and (restrict_sale_orders or restrict_sales_by_due_invoices) \
            and not ('website_id' in self and self.website_id is False):
            # Si el campo de permitir con límite excedido o vencido, pues ya no importa nada.
            if not self.allow_exceeding_credit_limit and not self.partner_id.commercial_partner_id.allow_override:
                if restrict_sale_orders:
                    today = fields.Date.today()
                    company_currency_id = self.company_id.currency_id
                    current_sale_amount = self.env['res.currency']._convert(
                        self.amount_total, self.company_id.currency_id, self.currency_id, today)
                    # balance = self.partner_id.commercial_partner_id.balance
                    credit_limit = self.partner_id.commercial_partner_id.credit_limit
                    available_credit_amount = self.partner_id.commercial_partner_id.available_credit_amount
                    credit = self.partner_id.commercial_partner_id.credit

                    # Si el cliente tiene límite de crédito mayor a 0
                    if available_credit_amount - current_sale_amount < 0:
                        raise ValidationError(
                            _("Credit limit exceeded by this customer. Please, contact to your "
                            "\"Credit & Collection Department\".\n"
                            "\n    Credit Limit: %s"
                            "\n    Credit: %s"
                            "\n    Available Credit: %s")
                            % (formatLang(self.env, credit_limit, currency_obj=company_currency_id),
                            formatLang(self.env, credit, currency_obj=company_currency_id),
                            formatLang(self.env, available_credit_amount, currency_obj=company_currency_id)))
                if restrict_sales_by_due_invoices:
                    credit_extra_days = self.partner_id.commercial_partner_id.credit_extra_days
                    today_with_extra_days = fields.date.today()-timedelta(days=credit_extra_days)
                    # Extraer todas las facturas vencidas del cliente
                    domain = [
                        ('invoice_date_due', '<', today_with_extra_days),
                        ('state', '=', 'posted'),
                        ('payment_state', 'in', ('not_paid', 'partial')),
                        ('move_type', '=', 'out_invoice'),
                        '|',
                        ('partner_id', '=', self.partner_id.id),
                        ('partner_id.commercial_partner_id', '=', self.partner_id.commercial_partner_id.id),
                    ]
                    # _logger.info(str(domain))
                    date_due_invoices_ids = self.env["account.move"].search(domain, limit=1)
                    _logger.info("Due invoices: %s" % str(date_due_invoices_ids))
                    if date_due_invoices_ids:
                        raise ValidationError(
                            _("This customer has at least one past due invoice including %s customer's extra days."
                                "\nPlease, contact to your \"Credit & Collection Department\".") % credit_extra_days)

        res = super(CreditLimitAlertSaleOrder, self).action_confirm()
        return res

    @api.onchange('allow_exceeding_credit_limit')
    def udpate_stock_moves(self):
        for sale in self._origin:
            for stock_picking in sale.picking_ids:
                stock_picking.write({'allow_exceeding_credit_limit': sale.allow_exceeding_credit_limit})


    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        warning = super(CreditLimitAlertSaleOrder, self).onchange_partner_id_warning()
        restrict_sales_by_due_invoices = self.company_id.restrict_sales_by_due_invoices
        if restrict_sales_by_due_invoices:
            credit_extra_days = self.partner_id.commercial_partner_id.credit_extra_days
            today_with_extra_days = fields.date.today()-timedelta(days=credit_extra_days)
            # Extraer todas las facturas vencidas del cliente
            domain = [
                ('invoice_date_due', '<', today_with_extra_days),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ('not_paid', 'partial')),
                ('move_type', '=', 'out_invoice'),
                '|',
                ('partner_id', '=', self.partner_id.id),
                ('partner_id.commercial_partner_id', '=', self.partner_id.commercial_partner_id.id),
            ]
            date_due_invoices_ids = self.env["account.move"].search(domain, limit=1)
            _logger.info("Due invoices: %s" % str(date_due_invoices_ids))
            if date_due_invoices_ids:
                message = _("This customer has at least one past due invoice including %s customer's extra days."
                        "\nPlease, contact to your \"Credit & Collection Department\".") % credit_extra_days
                if warning:
                    warning['warning']['message'] = message + '\n\n' + warning['warning']['message']
                else:
                    title = _("Warning for %s") % self.partner_id.name
                    warning = {
                            'title': title,
                            'message': message,
                    }
                    warning = {'warning': warning}

        return warning
