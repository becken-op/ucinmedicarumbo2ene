# -*- coding: utf-8 -*-
from odoo import fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    analytic_account_id = fields.Many2one(
        string="Analytic Account", comodel_name="account.analytic.account"
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    required_analytic_account_on_stock_scrap = fields.Boolean(
        string='Analytic account required',
        default=lambda self: self.env.company.required_analytic_account_on_stock_scrap,
        readonly=True,
        copy=False,
        help="If marked, analytic account field is required in scraps.")
    required_analytic_tags_on_stock_scrap = fields.Boolean(
        string='Analytic tags required',
        default=lambda self: self.env.company.required_analytic_tags_on_stock_scrap,
        readonly=True,
        copy=False,
        help="If marked, analytic tags field is required in scraps.")

    def _prepare_move_values(self):
        res = super()._prepare_move_values()
        res.update(
            {
                "analytic_account_id": self.analytic_account_id.id,
                "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            }
        )
        return res
