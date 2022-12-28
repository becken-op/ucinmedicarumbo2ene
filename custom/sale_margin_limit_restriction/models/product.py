# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Product(models.Model):
    _inherit = 'product.product'

    custom_margin_percent_sale = fields.Float(
        "Minimum Sales Margin (%)",
        copy=True,
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    custom_margin_percent_sale = fields.Float(
        "Minimum Sales Margin (%)",
        copy=True,
        compute='_compute_margin_percent_sale',
        inverse='_set_margin_percent_sale', store=True,
    )

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_margin_percent_sale(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.custom_margin_percent_sale = template.product_variant_ids.custom_margin_percent_sale
        for template in (self - unique_variants):
            template.custom_margin_percent_sale = False

    def _set_margin_percent_sale(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.custom_margin_percent_sale = template.custom_margin_percent_sale