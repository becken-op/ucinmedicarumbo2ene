# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    customer_portal_posted = fields.Boolean(
        string="Posted on portal",
        default=False,
        tracking=True,
        groups="bck_account_customer_portal_invoice_management.group_customer_portal_user",
        help="If marked, this invoice was already posted on the customer portal.")
    customer_portal_posting_required = fields.Boolean(
        string="Posting invoices on customer portal",
        related='partner_id.commercial_partner_id.customer_portal_posting_required',
        store=True,
        groups="bck_account_customer_portal_invoice_management.group_customer_portal_user",
        help="If marked, requires posting invoices on customer portal.")
