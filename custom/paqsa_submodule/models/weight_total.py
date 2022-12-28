#-*- coding: utf-8 -*-
from odoo import models, fields, api

class weighttotal(models.Model):
    _name = 'weight.total'
    
    uom_medida = fields.Many2one('uom.uom')
    total_weight_per_uom = fields.Float(string='cantidad')
    picking_id = fields.Many2one(
        'stock.picking',
        string='Picking'
    )