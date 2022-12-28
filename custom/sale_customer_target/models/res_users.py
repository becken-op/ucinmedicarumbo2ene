""" Inherit res Partner to Add Sale Target """

from odoo import fields, models


class ResUsers(models.Model):
    """
        Inherit res Partner:
         - to Add Customer Target
    """
    _inherit = 'res.users'

    target_ids = fields.One2many(
        'sale.customer.target',
        'user_id'
    )
