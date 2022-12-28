# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
import logging
from odoo.tools.misc import formatLang

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    warn_msg =fields.Text(
        string='Warning Msg',
        compute="generate_warn_msg",
    )
    
    custom_is_confirm= fields.Boolean(
        string="Are You Sure Confirm for Create Sheets ?",
    )
    
    #@api.multi
    def check_budge_account(self):
        for rec in self:
            custom_date = rec.date_order or fields.date.today()
            account_budget_line_ids = self.env['crossovered.budget.lines'].sudo().search(
                 [('date_from', '<=', custom_date),
                 ('date_to','>=', custom_date),
                 ('crossovered_budget_state', 'not in', ('draft','cancel','done','confirm')),
                 ('company_id', 'in', rec.company_id.ids)])
        return account_budget_line_ids
    
    #@api.multi
    def _stop_method(self):
        account_budget_line_ids = self.check_budge_account()
        stop_msg = warn_msg = ''
        account_budget_line_list_stop  = []
        account_budget_line_list_warn = []
        header_msg = _('Budget Exceed Alert: \n')
        new_string = header_msg.center(500)
        for order_line in self.order_line:
            for account_budget_line in account_budget_line_ids:
                budget_line_ids  = account_budget_line.filtered(
                    lambda m: m.analytic_account_id == order_line.account_analytic_id
                    and (order_line.product_id.property_account_expense_id in m.general_budget_id.account_ids or order_line.product_id.categ_id.property_account_expense_categ_id in m.general_budget_id.account_ids))
                if budget_line_ids:
                    practical_amount = sum(line.practical_amount for line in budget_line_ids)
                    budget_currency_price = self.currency_id._convert(
                        order_line.price_subtotal, 
                        account_budget_line.currency_id, 
                        account_budget_line.company_id,
                        account_budget_line.create_date
                    )
                    total_practical_amount = practical_amount + budget_currency_price

                    if account_budget_line.custom_configuration_state in ['warn', 'warn_stop']:
                        _logger.info("total_practical_amount: %s, practical_amount: %s" % (total_practical_amount, practical_amount))
                        budget_current_percentaje = round(abs(total_practical_amount/account_budget_line.planned_amount)*100, 2)
                        if budget_current_percentaje > self.company_id.budget_warning_percentage:
                            account_budget_line_list_warn.append(account_budget_line)
                            practical_amount_str = formatLang(self.env, abs(total_practical_amount), currency_obj=account_budget_line.currency_id)
                            planned_amount_str = formatLang(self.env, abs(account_budget_line.planned_amount), currency_obj=account_budget_line.currency_id)
                            warn_msg += _('* Account "%s", Analytic Account "%s" exceeds the %s%% warning percentage, budget: %s (%s vs %s wich represents %s%%).\n') % (order_line.product_id.categ_id.property_account_expense_categ_id.name, account_budget_line.analytic_account_id.name, self.company_id.budget_warning_percentage, account_budget_line.crossovered_budget_id.name, planned_amount_str, practical_amount_str, budget_current_percentaje)
                    if abs(account_budget_line.planned_amount) < abs(total_practical_amount):
                        if account_budget_line.custom_configuration_state in ['stop', 'warn_stop']:
                            account_budget_line_list_stop.append(account_budget_line)
                            practical_amount_str = formatLang(self.env, abs(total_practical_amount), currency_obj=account_budget_line.currency_id)
                            planned_amount_str = formatLang(self.env, abs(account_budget_line.planned_amount), currency_obj=account_budget_line.currency_id)
                            stop_msg += _('* Account "%s", Analytic Account "%s" exceeds budget: %s (%s vs %s).\n') % (order_line.product_id.categ_id.property_account_expense_categ_id.name, account_budget_line.analytic_account_id.name, account_budget_line.crossovered_budget_id.name, planned_amount_str, practical_amount_str)
                                   
        stop_msg_config = new_string + stop_msg
        warn_msg_config = warn_msg
        return stop_msg_config, account_budget_line_list_stop, warn_msg_config, account_budget_line_list_warn


    def button_confirm(self):
        account_budget_line_ids = self.check_budge_account()
        self._stop_method()
        if account_budget_line_ids:
            stop_msg_config, account_budget_line_list, warn_msg_config, account_budget_line_list_warn = self._stop_method()
            for account_budget_line in account_budget_line_ids:
                custom_crossovered_budget_id = account_budget_line.crossovered_budget_id
                for budget_line in account_budget_line_list:
                    if stop_msg_config:
                        if any([ptype in ['stop', 'warn_stop'] for ptype in custom_crossovered_budget_id.mapped('crossovered_budget_line.custom_configuration_state')]):
                            raise UserError((stop_msg_config))
                if all([ptype in ['ignore'] for ptype in custom_crossovered_budget_id.mapped('crossovered_budget_line.custom_configuration_state')]):
                    res = super(PurchaseOrder, self).button_confirm()
                    return res
                elif any([ptype in ['warn', 'warn_stop'] for ptype in custom_crossovered_budget_id.mapped('crossovered_budget_line.custom_configuration_state')]):
                    res = super(PurchaseOrder, self).button_confirm()
                    return res
                else:
                    return super(PurchaseOrder, self).button_confirm()
        else:
            res = super(PurchaseOrder, self).button_confirm()
            return res


    @api.depends('order_line')
    def generate_warn_msg(self):
        warn_msg = ''
        stop_msg_config, account_budget_line_list_stop, warn_msg_config, account_budget_line_list_warn= self._stop_method()
        for account_budget_line in account_budget_line_list_warn:
            custom_crossovered_budget_id = account_budget_line.crossovered_budget_id

            # if not account_budget_line_list_stop:
            if any([ptype in ['warn', 'warn_stop'] for ptype in custom_crossovered_budget_id.mapped('crossovered_budget_line.custom_configuration_state')]):
                if account_budget_line.custom_configuration_state in ['warn', 'warn_stop']:
                    warn_msg = warn_msg_config
        self.warn_msg = warn_msg
        if self.warn_msg == '':
            self.write({'custom_is_confirm': False})
        else:
            self.write({'custom_is_confirm': True})
