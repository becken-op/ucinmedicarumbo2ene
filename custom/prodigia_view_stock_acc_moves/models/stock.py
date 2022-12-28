# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import datetime
import pdb
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    account_move_count = fields.Integer(string="No. de movimientos contables",
                                        compute="_compute_account_move_count")


    def _compute_account_move_count(self):
        for rec in self:
            acc_moves = rec.mapped('move_ids_without_package.account_move_ids')
            rec.account_move_count = len(set(acc_moves))



    def action_view_account_moves(self):
        acc_moves = self.mapped('move_ids_without_package.account_move_ids')
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if len(acc_moves) > 1:
            action['domain'] = [('id', 'in', acc_moves.ids)]
        elif len(acc_moves) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = acc_moves.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action



