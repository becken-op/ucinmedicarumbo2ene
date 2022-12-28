# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_restrict_compare_margin_custom = fields.Boolean(
        string="Allow Minimum Margin Difference?",
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}
    )

    def _custom_sale_margin_limit(self):
        for order in self:
            # if not order._context.get('skip_margin_warning') and not order.is_restrict_compare_margin_custom and not order.website_id:
            if not order._context.get('skip_margin_warning') and not order.is_restrict_compare_margin_custom:
                sale_order_lines = order.order_line.filtered(lambda l: (l.product_id.categ_id.custom_margin_percent_sale) > l.margin_percent and l.product_id.categ_id.custom_margin_percent_sale != 0)
                product_to_checklines = order.order_line - sale_order_lines
                if product_to_checklines:
                    sale_order_lines += product_to_checklines.filtered(lambda l: (l.product_id.custom_margin_percent_sale) > l.margin_percent and l.product_id.custom_margin_percent_sale != 0)
                product_list = []
                for sol in sale_order_lines:
                    product_list.append(sol.product_id.display_name)
                if product_list:
                    product_str = ' , '.join(map(str, product_list))
                    raise UserError(_("Minimum margin set on a product does not match with computed margin on sales order line for product: %s")%product_str)    
        return True
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm() 
        self._custom_sale_margin_limit()
        return res