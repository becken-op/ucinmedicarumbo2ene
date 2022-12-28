# -*- coding: utf-8 -*-group_sale_margin
from odoo import models


class Website(models.Model):
    _inherit = 'website'


    def _prepare_sale_order_values(self, partner, pricelist):
        self.ensure_one()
        values = super(Website, self)._prepare_sale_order_values(partner, pricelist)

        branch_id = partner.branch_id
        warehouse_id = False
        if branch_id:
            branched_warehouse = self.env['stock.warehouse'].sudo().search([('branch_id', '=', branch_id.id)])
            if branched_warehouse:
                warehouse_id = branched_warehouse.ids[0]

        new_values = {
            'warehouse_id': warehouse_id,
            'branch_id': branch_id.id,
            'l10n_mx_edi_usage': partner.commercial_partner_id.l10n_mx_edi_usage,
            'l10n_mx_edi_payment_method_id': partner.commercial_partner_id.l10n_mx_edi_payment_method_id.id,
        }
        values.update(new_values)

        return values
