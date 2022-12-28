# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    currency_id = fields.Many2one(
        string="Currency", related="inventory_id.company_id.currency_id"
    )
    adjustment_cost = fields.Monetary(
        string="Adjustment cost", compute="_compute_adjustment_cost", store=True
    )

    @api.depends("difference_qty", "inventory_id.state")
    def _compute_adjustment_cost(self):
        for record in self:
            record.adjustment_cost = (
                record.difference_qty * record.product_id.standard_price
            )

    def action_validate(self):
        if not self.exists():
            return
        self.ensure_one()
        if not self.user_has_groups('stock.group_stock_manager'):
            raise UserError(_("Only a stock manager can validate an inventory adjustment."))
        if self.state != 'confirm':
            raise UserError(_(
                "You can't validate the inventory '%s', maybe this inventory "
                "has been already validated or isn't ready.", self.name))
        inventory_lines = self.line_ids.filtered(lambda l: l.product_id.tracking in ['lot', 'serial'] and not l.prod_lot_id and l.theoretical_qty != l.product_qty)
        lines = self.line_ids.filtered(lambda l: float_compare(l.product_qty, 1, precision_rounding=l.product_uom_id.rounding) > 0 and l.product_id.tracking == 'serial' and l.prod_lot_id)
        if inventory_lines and not lines:
            wiz_lines = [(0, 0, {'product_id': product.id, 'tracking': product.tracking}) for product in inventory_lines.mapped('product_id')]
            wiz = self.env['stock.track.confirmation'].create({'inventory_id': self.id, 'tracking_line_ids': wiz_lines})
            return {
                'name': _('Tracked Products in Inventory Adjustment'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'res_model': 'stock.track.confirmation',
                'target': 'new',
                'res_id': wiz.id,
            }
        self._action_done()
        self.line_ids._check_company()
        self._check_company()
        return True


class StockInventoryTierValidation(models.Model):
    _name = 'stock.inventory.tier.validation'
    _description = 'Stock Inventory Tier Validation'
    _order = 'adjustment_cost_from, adjustment_cost_to, group_id'
    _rec_name = 'group_id'

    group_id = fields.Many2one(
        'delivery.carrier',
        string='Delivery Carrier',
        required=True,
        help='')
    authorized_group_id = fields.Many2one(
        'res.groups',
        string='Authorized Group',
        required=True,
        help='')
    adjustment_cost_from = fields.Monetary(
        string="Adjustment Cost From",
        digits="Product Price",
        currency_field='currency_id',
    )
    adjustment_cost_to = fields.Monetary(
        string="Adjustment Cost To",
        digits="Product Price",
        currency_field='currency_id',
    )
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True,
        default=lambda
            self: self.env.company.currency_id.id)
