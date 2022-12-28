# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    
    @api.model
    def default_get(self,fields):
        res = super(SaleOrder, self).default_get(fields)
        branch_id = warehouse_id = False
        if self.env.user.branch_id:
            branch_id = self.env.user.branch_id.id
        if branch_id:
            branched_warehouse = self.env['stock.warehouse'].search([('branch_id','=',branch_id)])
            if branched_warehouse:
                warehouse_id = branched_warehouse.ids[0]
        else:
            warehouse_id = self._default_warehouse_id()
            warehouse_id = warehouse_id.id

        res.update({
            'branch_id' : branch_id,
            'warehouse_id' : warehouse_id,
            })

        return res

    branch_id = fields.Many2one('res.branch', string="Branch")

    
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['branch_id'] = self.branch_id.id
        return res


    # JCT
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        selected_partner_id = self.partner_id
        res = {}
        if selected_partner_id and selected_partner_id.branch_id:
            if self.env.user.branch_id.id != selected_partner_id.branch_id.id:
                res = {'warning': {
                    'title': _('Warning'),
                    'message': _("The selected customer belongs to branch %s.") % selected_partner_id.branch_id.name,
                }}
        if res:
            return res


    @api.depends('branch_id')
    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        selected_brach = self.branch_id
        if selected_brach:            
            # JCT 4 lines
            warehouse_id = self.env['stock.warehouse'].search(
                [('branch_id', '=', selected_brach.id)], limit=1)
            if warehouse_id:
                _logger.info('Warehouse onchange branch_id: ' + warehouse_id.name)
                self.warehouse_id = warehouse_id

            user_id = self.env['res.users'].browse(self.env.uid)
            user_branch = user_id.sudo().branch_id
            if user_branch and user_branch.id != selected_brach.id:
                raise Warning("Please select active branch only. Other may create the Multi branch issue. \n\ne.g: If you wish to add other branch then Switch branch from the header and set that.")
    
    # @api.onchange('warehouse_id')
    # def _onchange_warehouse_id(self):
    #     selected_warehouse_id = self.warehouse_id
    #     if selected_warehouse_id:
    #         if self.warehouse_id.branch_id != self.branch_id:
    #             raise Warning("Please select a warehouse that belongs to the document branch.")
