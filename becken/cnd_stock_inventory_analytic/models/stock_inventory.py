# -*- coding: utf-8 -*-
from odoo import fields, models


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account')
    analytic_tag_ids = fields.Many2many(
        "account.analytic.tag",
        string="Analytic Tags")
    required_analytic_account_on_stock_inventory = fields.Boolean(
        string='Analytic account required',
        default=lambda self: self.env.company.required_analytic_account_on_stock_inventory,
        readonly=True,
        help="If marked, analytic account field is required in inventory adjusments.")
    required_analytic_tags_on_stock_inventory = fields.Boolean(
        string='Analytic tags required',
        default=lambda self: self.env.company.required_analytic_tags_on_stock_inventory,
        readonly=True,
        help="If marked, analytic tags field is required in inventory adjusments.")

class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        self.ensure_one()
        vals = super(StockInventoryLine, self)._get_move_values(qty, location_id, location_dest_id, out)
        if self.inventory_id.analytic_account_id:
            vals['analytic_account_id'] = self.inventory_id.analytic_account_id.id
        if self.inventory_id.analytic_tag_ids:
            vals['analytic_tag_ids'] = [(6, 0, self.inventory_id.analytic_tag_ids.ids)]
        return vals
