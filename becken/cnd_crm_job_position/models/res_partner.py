# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.onchange('job_position_id')
    def onchange_job_position(self):
        for partner in self:
            if partner.job_position_id:
                partner.function = partner.job_position_id.name