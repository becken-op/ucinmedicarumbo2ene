from odoo import models, fields, api, _

class CreditLimitAlertResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    credit_limit = fields.Monetary('Limite de credito')
    credit_available = fields.Monetary('Cedito disponible', compute='_compute_amount_credit_available')
    block_sales = fields.Boolean('Bloquear Ventas', default=False)

    @api.depends('credit_limit','credit_available','credit')
    def _compute_amount_credit_available(self):
        for rec in self:
            rec.credit_available = rec.credit_limit - rec.credit
            pass
        
    def call_wizard(self):
        wizard_form = self.env.ref('credit_limit_alert.credit_limit_alert_partner_statement_wizard_view', False)
        view_id = self.env['credit_limit_alert.partner_statement_wizard']
        vals = {
            'name': 'this is for set name',
            'str_partner_id': self.id,
        }
        new = view_id.create(vals)
        return {
            'name': _('Reporte de estado de deudas de ' + self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'credit_limit_alert.partner_statement_wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }


