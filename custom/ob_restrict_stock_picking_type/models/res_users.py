# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_picking_type_ids = fields.Many2many('stock.picking.type', 'rel_user_picking_type', 'user_id',
                                                'picking_type_id',
                                                string="Allowed Operation Types")
