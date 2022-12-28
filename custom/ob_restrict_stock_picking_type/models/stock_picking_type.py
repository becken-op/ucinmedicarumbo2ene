from odoo import models, fields, api


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    user_ids = fields.Many2many('res.users', 'rel_user_picking_type', 'picking_type_id', 'user_id',
                                string="Allowed Users")