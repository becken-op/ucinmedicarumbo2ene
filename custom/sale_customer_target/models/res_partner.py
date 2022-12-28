""" Inherit res Partner to Add Sale Target """

from odoo import fields, models


class ResPartner(models.Model):
    """
        Inherit res Partner:
         - to Add Customer Target
    """
    _inherit = 'res.partner'

    target_ids = fields.One2many(
        'sale.customer.target',
        'partner_id'
    )
