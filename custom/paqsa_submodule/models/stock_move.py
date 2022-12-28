#-*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from collections import defaultdict

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    name_account_id = fields.Char(
        'Factura nro')


    @api.model
    def _consuming_picking_types(self):
        return ['outgoing','internal']

    @api.model
    def default_get(self, fields_list):
        # We override the default_get to make stock moves created after the picking was confirmed
        # directly as available in immediate transfer mode. This allows to create extra move lines
        # in the fp view. In planned transfer, the stock move are marked as `additional` and will be
        # auto-confirmed.
        defaults = super(StockMove, self).default_get(fields_list)
        if self.env.context.get('default_picking_id'):
            picking_id = self.env['stock.picking'].browse(self.env.context['default_picking_id'])
            if picking_id.state == 'done':
                defaults['state'] = 'done'
                defaults['product_uom_qty'] = 0.0
                defaults['additional'] = True
            elif picking_id.state not in ['cancel', 'assigned', 'done']:
                if picking_id.immediate_transfer:
                    defaults['state'] = 'draft'
                defaults['product_uom_qty'] = 0.0
                defaults['additional'] = True  # to trigger `_autoconfirm_picking`
        return defaults