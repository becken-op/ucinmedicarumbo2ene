# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    branch_ids = fields.Many2many('res.branch',string="Allowed Branch")
    branch_id = fields.Many2one('res.branch', string= 'Branch')

    def write(self, values):
        if 'branch_id' in values or 'branch_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
        user = super(ResUsers, self).write(values)
        return user

    def _get_default_warehouse_id(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        user_branch = user_id.sudo().branch_id

        if self.property_warehouse_id and self.property_warehouse_id.branch_id == user_branch:
            return self.property_warehouse_id
        # !!! Any change to the following search domain should probably
        # be also applied in sale_stock/models/sale_order.py/_init_column.
        warehouse_id = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id), ('branch_id', '=', user_branch.id)], limit=1)
        if warehouse_id:
            return warehouse_id
        else:
            return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
