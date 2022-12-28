# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'product.pricelist.item'


    base = fields.Selection(
        selection_add=[
            ('most_cost_price','Precio del Proveedor')],
            ondelete = {'most_cost_price': 'cascade'}
            )


