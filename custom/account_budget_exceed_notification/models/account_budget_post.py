# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class BudgetPost(models.Model):
    _inherit = 'account.budget.post'

    custom_notify_users_ids = fields.Many2many(
        'res.users',
        string="Exceed Limit Notify Users",
        copy=True
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
