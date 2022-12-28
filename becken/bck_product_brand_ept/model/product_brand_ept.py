# -*- coding: utf-8 -*-
"""
    This model is used to create a product brand fields
"""
from odoo import api, fields, models


class ProductBrandEpt(models.Model):
    _name = 'product.brand.ept'
    _description = 'Product Brand'
    _order = 'name'
    
    name = fields.Char('Brand Name', required=True)
    description = fields.Text('Description', translate=True)
    logo = fields.Binary('Logo File')
    product_ids = fields.One2many(
        'product.template', 'product_brand_ept_id', string="Brand Products", readonly=True)
    products_count = fields.Integer(
        string='Number of products',
        compute='_compute_products_count',
        help='It shows the number of product counts',
    )
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of product Brands.", index=True,
                              default=10)

    @api.depends('product_ids')
    def _compute_products_count(self):
        """
        product count computation
        @return:
        """
        for brand in self:
            brand.products_count = len(brand.product_ids)

    def set_brand_wizard(self):
        """
        action brand wizard
        @return: wizard-action
        """
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.brand.config',
            'name': "Product Brand Configuration",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(default_brand_id=self.id),
        }
        return action
