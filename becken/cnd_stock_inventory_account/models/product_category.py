# -*- coding: utf-8 -*-
from odoo import fields, models

ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]"


class ProductCategory(models.Model):
    _inherit = "product.category"

    property_stock_adjustment_in_account_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Incoming Account",
        domain=ACCOUNT_DOMAIN,
        help="This incoming account will be used when validating a stock adjustment.")
    property_stock_adjustment_out_account_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Outgoing Account",
        domain=ACCOUNT_DOMAIN,
        help="This outgoing account will be used when validating a stock adjustment.")


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_src_account(self, accounts_data):
        if self.inventory_id:
            return self.product_id.product_tmpl_id.categ_id.property_stock_adjustment_out_account_id.id or \
                self.location_id.valuation_out_account_id.id or accounts_data['stock_input'].id
        else:
            return super(StockMove, self)._get_src_account(accounts_data)

    def _get_dest_account(self, accounts_data):
        if self.inventory_id:
            return self.product_id.product_tmpl_id.categ_id.property_stock_adjustment_in_account_id.id or \
                self.location_dest_id.valuation_in_account_id.id or accounts_data['stock_output'].id
        else:
            return super(StockMove, self)._get_dest_account(accounts_data)
