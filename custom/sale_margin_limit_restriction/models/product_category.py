# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = "product.category"

    custom_margin_percent_sale = fields.Float(
        "Minimum Sales Margin (%)",
        copy=True
    )