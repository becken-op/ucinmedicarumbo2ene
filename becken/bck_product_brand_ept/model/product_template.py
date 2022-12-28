# -*- coding: utf-8 -*-
"""
    This model is used to show the tab line filed in product template
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """
    Class for product template
    """
    _inherit = "product.template"

    product_brand_ept_id = fields.Many2one(
        'product.brand.ept',
        string='Brand',
        help='Select a brand for this product',
    )
