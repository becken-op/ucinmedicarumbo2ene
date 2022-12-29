# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResGroups(models.Model):
    _inherit = 'res.groups'


    #def _get_allowed_picking_type_ids(self):
    #    for rec in self:
    #        query = "SELECT pt.picking_type_id " \
    #                "FROM group_picking_type_rel  as pt join stock_picking_type as p " \
    #                "on p.id=pt.picking_type_id WHERE pt.group_id=%s and p.active=true;"
    #        args = [rec.id]
    #        self.env.cr.execute(query, args)
    #        allowed_picking_type_ids = [picking['picking_type_id'] for picking in self.env.cr.dictfetchall()]
    #        rec.allowed_picking_type_ids = [(6, 0, allowed_picking_type_ids)]

    #allowed_picking_type_ids = fields.Many2many('stock.picking.type',string="Allowed Operation Types", compute="_get_allowed_picking_type_ids")
    allowed_picking_type_ids = fields.Many2many('stock.picking.type', 'group_picking_type_rel', 'group_id',
                                                'picking_type_id',
                                                string="Allowed Operation Types")