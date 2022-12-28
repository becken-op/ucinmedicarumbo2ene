# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    # To this case the options in selection field are in Spanish, because are
    # only three options and We need that value to set in the CFDI
    l10n_mx_cfdi_tax_key = fields.Selection(
        [('001', '001'),
         ('002', '002'),
         ('003', '003')], 'Tax Key',
        help='The CFDI version 3.3 have the attribute "Impuesto" in the tax '
        'lines. The Tax Catalog specifies which are the Tax Keys transferred and '
        'taxes withheld, linked to the concepts of Digital Tax Receipts on the Internet.')
