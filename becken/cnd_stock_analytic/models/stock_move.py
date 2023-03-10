# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one(
        string="Analytic Account",
        comodel_name="account.analytic.account",
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    required_analytic_account_on_stock_move = fields.Boolean(
        string='Analytic account required',
        default=lambda self: self.env.company.required_analytic_account_on_stock_move,
        readonly=True,
        copy=False,
        help="If marked, analytic account field is required in stock moves.")
    required_analytic_tags_on_stock_move = fields.Boolean(
        string='Analytic tags required',
        default=lambda self: self.env.company.required_analytic_tags_on_stock_move,
        readonly=True,
        copy=False,
        help="If marked, analytic tags field is required in stock moves.")


    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, description
    ):
        self.ensure_one()
        res = super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, description
        )
        for line in res:
            if (
                line[2]["account_id"]
                != self.product_id.categ_id.property_stock_valuation_account_id.id
            ):
                # Add analytic account in debit line
                if self.analytic_account_id:
                    line[2].update({"analytic_account_id": self.analytic_account_id.id})
                # Add analytic tags in debit line
                if self.analytic_tag_ids:
                    line[2].update(
                        {"analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)]}
                    )
        return res

    def _prepare_procurement_values(self):
        """
        Allows to transmit analytic account from moves to new
        moves through procurement.
        """
        res = super()._prepare_procurement_values()
        if self.analytic_account_id:
            res.update(
                {
                    "analytic_account_id": self.analytic_account_id.id,
                }
            )
        return res

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        fields = super()._prepare_merge_moves_distinct_fields()
        fields.append("analytic_account_id")
        return fields

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
        We fill in the analytic account when creating the move line from
        the move
        """
        res = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        if self.analytic_account_id:
            res.update({"analytic_account_id": self.analytic_account_id.id})
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", related="move_id.analytic_account_id")

    @api.model
    def _prepare_stock_move_vals(self):
        """
        In the case move lines are created manually, we should fill in the
        new move created here with the analytic account if filled in.
        """
        res = super()._prepare_stock_move_vals()
        if self.analytic_account_id:
            res.update({"analytic_account_id": self.analytic_account_id.id})
        return res
