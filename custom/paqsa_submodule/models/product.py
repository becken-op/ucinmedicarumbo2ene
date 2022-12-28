# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template',
        auto_join=True, index=True, ondelete='cascade', required=True)
        
    most_cost_price = fields.Float(
        'Proveedor mas costoso', 
        compute='_compute_most_cost_price',
        store=True)
    
    @api.depends('seller_ids', 'variant_seller_ids', 'product_variant_count','variant_seller_ids.price','seller_ids.price')
    def _compute_most_cost_price(self):
        for rec in self:
            seller_price = 0
            lista = list()
            product_variant_count = rec.product_variant_count
            if product_variant_count >= 2 :
                for product in rec.variant_seller_ids:
                    price = product.price
                    lista.append(price)
                    for p in range(0,len(lista)):
                        if lista[p]> seller_price:
                            seller_price = lista[p]
                        rec.most_cost_price = seller_price
            if product_variant_count < 2:
                for product in rec.seller_ids:
                    price = product.price
                    lista.append(price)
                    for p in range(0,len(lista)):
                        if lista[p]> seller_price:
                            seller_price = lista[p]
                        rec.most_cost_price = seller_price

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    most_cost_price = fields.Float(
        'Proveedor mas costoso', 
        compute='_compute_most_cost_price',
        store=True)

    @api.depends('seller_ids', 'variant_seller_ids', 'product_variant_count','variant_seller_ids.price','seller_ids.price')
    def _compute_most_cost_price(self):
        for rec in self:
            seller_price = 0
            lista = list()
            product_variant_count = rec.product_variant_count
            if product_variant_count >= 2 :
                for product in rec.variant_seller_ids:
                    price = product.price
                    lista.append(price)
                    for p in range(0,len(lista)):
                        if lista[p]> seller_price:
                            seller_price = lista[p]
                        rec.most_cost_price = seller_price
            if product_variant_count < 2:
                for product in rec.seller_ids:
                    price = product.price
                    lista.append(price)
                    for p in range(0,len(lista)):
                        if lista[p]> seller_price:
                            seller_price = lista[p]
                        rec.most_cost_price = seller_price