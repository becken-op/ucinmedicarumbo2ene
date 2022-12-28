# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    customer_number = fields.Char(string='Customer Number', size=6,
        help='Customer Number in your Bank.')
