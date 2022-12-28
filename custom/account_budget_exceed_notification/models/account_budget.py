# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class Budget(models.Model):
    _inherit = 'crossovered.budget'

    custom_notify_users_ids = fields.Many2many(
        'res.users',
        string="Exceed Limit Notify Users",
        copy=True,
    )


class BudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    is_custom_sent_exceed_notify_mail = fields.Boolean(
        string='Sent Exceed Notify Email',
        copy=False,
    )

    def _compute_practical_amount(self):
        result = super(BudgetLines, self)._compute_practical_amount()
        for line in self.filtered(lambda line:not line.is_custom_sent_exceed_notify_mail and line.planned_amount > 0.0 and line.planned_amount < line.practical_amount):
            template_id = self.env.ref("account_budget_exceed_notification.mail_templ_budget_exeed_notify_template_custom")
            template_id.send_mail(line.id)
            line.is_custom_sent_exceed_notify_mail = True
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
