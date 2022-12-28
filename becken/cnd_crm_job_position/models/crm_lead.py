# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    job_position_id = fields.Many2one(
        "res.partner.job_position", "Categorized job position"
    )

    @api.onchange('job_position_id')
    def onchange_job_position(self):
        for lead in self:
            if lead.job_position_id:
                lead.function = lead.job_position_id.name

    
    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        # OVERRIDE
        res = super(CrmLead, self)._prepare_customer_values(partner_name, is_company=is_company, parent_id=parent_id)
        res.update({'job_position_id': self.job_position_id.id})
        return res
