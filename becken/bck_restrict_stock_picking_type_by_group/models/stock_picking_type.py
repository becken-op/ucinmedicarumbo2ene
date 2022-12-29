from odoo import models, fields, api


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    group_ids = fields.Many2many('res.groups', 'group_picking_type_rel', 'picking_type_id', 'group_id',
                                string="Allowed Groups")