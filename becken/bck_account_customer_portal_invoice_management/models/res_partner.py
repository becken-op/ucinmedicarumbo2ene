# -*- coding: utf-8 -*-
from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    customer_portal_posting_required = fields.Boolean(
        string="Post invoices on portal",
        default=False,
        groups="bck_account_customer_portal_invoice_management.group_customer_portal_user",
        help="If marked, requires posting invoices on customer portal.")
    portal_url = fields.Char(
        string='Portal Address',
        groups="bck_account_customer_portal_invoice_management.group_customer_portal_user")
    portal_user = fields.Char(
        string='Portal User',
        groups="bck_account_customer_portal_invoice_management.group_customer_portal_user")
    portal_password = fields.Char(
        string='Portal Password',
        groups="bck_account_customer_portal_invoice_management.group_customer_portal_user")