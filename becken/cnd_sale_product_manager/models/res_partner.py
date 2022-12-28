# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    product_manager_id = fields.Many2one('res.users', string='Product Manager',
        help='The internal user in charge of this products contact.')
