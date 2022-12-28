# -*- coding: utf-8 -*-

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class UtmCampaign(models.Model):
    _name = 'utm.campaign'
    _inherit = ['utm.campaign', 'mail.thread', 'mail.activity.mixin']


    active = fields.Boolean(default=True, help="The active field allows you to hide the campaign without removing it.")
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date(string='End Date', default=fields.Date.today() + relativedelta(years=1), required=True)

	# Método para inactivar automáticamente campañas con fecha final vencida
    @api.model
    def action_inactivate_expired_utm_campaign(self):
        today = fields.Date.today()
        domain = [
			("active", "=", True),
			("end_date", "<", today),
        ]
        campaign_ids = self.env['utm.campaign'].search(domain)
        campaign_ids.write({'active': False})
