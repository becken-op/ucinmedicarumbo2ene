# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    manufacturing_date = fields.Date(string="Manufacturing date", tracking=True)
    product_expiration_time = fields.Integer(string='Expiration Time',
        related = 'product_id.expiration_time',
        help='Number of days after the receipt of the products (from the vendor'
        ' or in stock after production) after which the goods may become dangerous'
        ' and must not be consumed. It will be computed on the lot/serial number.')


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    manufacturing_date = fields.Date(related='lot_id.manufacturing_date', store=True, readonly=False)
    product_expiration_time = fields.Integer(string='Expiration Time',
        related = 'product_id.expiration_time',
        help='Number of days after the receipt of the products (from the vendor'
        ' or in stock after production) after which the goods may become dangerous'
        ' and must not be consumed. It will be computed on the lot/serial number.')

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        res = super()._get_inventory_fields_write()
        res += ['manufacturing_date']
        return res
    
    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        res = super()._get_inventory_fields_create()
        res.append('manufacturing_date')
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    manufacturing_date = fields.Date(string="Manufacturing date", tracking=True)
    product_expiration_time = fields.Integer(string='Expiration Time',
        related = 'product_id.expiration_time',
        help='Number of days after the receipt of the products (from the vendor'
        ' or in stock after production) after which the goods may become dangerous'
        ' and must not be consumed. It will be computed on the lot/serial number.')
    product_brand_ept_id = fields.Many2one(
        'product.brand.ept',
        string='Brand',
        related='product_id.product_brand_ept_id',
        store=True,
        help='Select a brand for this product',
    )

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        super()._onchange_lot_id()
        if not self.picking_type_use_existing_lots or not self.product_id.use_expiration_date:
            return
        if self.lot_id:
            self.manufacturing_date = self.lot_id.manufacturing_date
        else:
            self.expiration_date = False

    def _get_value_production_lot(self):
        res = super()._get_value_production_lot()
        if self.expiration_date:
            res.update({
                'manufacturing_date': self.manufacturing_date,
            })
        return res
