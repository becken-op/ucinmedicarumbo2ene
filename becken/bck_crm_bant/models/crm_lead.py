# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    budget = fields.Many2many(
        'criterios.budget',
        string="Budget",
        tracking=True,
        help="Presupuesto con el que cuenta el cliente")
    authority = fields.Many2many(
        'criterios.authority',
        string="Authority",
        tracking=True,
        help="Si se tiene contacto directo con los tomadores de decisiones")
    need = fields.Selection([
        ('25', '25% si está en problemas'),
        ('20', '20% si está en crecimiento'),
        ('10', '10% si está en estabilidad'),
        ('0', '0% si está en zona de confort')],
        string="Need",
        tracking=True,
        help="En que momento de la necesidad de encuentran: en problemas, en crecimiento, en estabilidad y zona de confort")
    time = fields.Selection([
        ('25', '25%: de 0 a 30 días'),
        ('20', '20%: de 30 a 90 días'),
        ('10', '10%: de 90 a 180 días'),
        ('0', '0%: más de 180 días'), ],
        string="Time",
        readonly=True,
        help="En cuanto tiempo estimamos que se genere la venta.")
    bant_score = fields.Integer(
        string="Puntuación Bant", compute="calculo_puntuacion", store=True)
    bant_actvity_sent = fields.Boolean(
        string="Bant Activity Sent", default=False)
    bant_score_below_threshold = fields.Boolean(
        string="Bant Below Threshold", compute="compute_bant_score_below_threshold", store=True)
    opportunity_type_id = fields.Many2one(
        'crm.lead.type',
        tracking=True,
        string="Type",
        help="")
    opportunity_type_not_editable = fields.Boolean(
        string="Type Not Editable", related='opportunity_type_id.not_editable')
    opportunity_classification_id = fields.Many2one(
        'crm.lead.classification',
        tracking=True,
        string="Classification",
        help="")
    # shipping_mode = fields.Selection([
    #     ('rel', 'REL'),
    #     ('rho', 'RHO'),
    #     ('rdi', 'RDI'),
    #     ('pco', 'PCO'),
    #     ('ppa', 'PPA'),
    #     ('eav', 'EAV'),
    #     ('epr', 'EPR'),
    #     ('eur', 'EUR'),],
    #     string='Shipping mode',
    #     help='REL: Recolección\n'
    #         'RHO: Ruta UCIN Hospitales\n'
    #         'RDI: Ruta UCIN Distribuidores\n'
    #         'PCO: Paqueteria con cobro\n'
    #         'PPA: Paqueteria pagada por UCIN\n'
    #         'EAV: Entrega Asesor de Ventas asignado\n'
    #         'EPR: Entrega programada\n'
    #         'EUR: Urgencia por error de UCIN\n',
    # )

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     """
    #     Update the following fields when the partner is changed:
    #     - shipping_mode
    #     """
    #     if self.partner_id:
    #         self.shipping_mode = self.partner_id.commercial_partner_id.shipping_mode
    #     else:
    #         self.shipping_mode = False

    # OVERRIDE If BANT Data is needed in "Convert to Opportunity" Wizard
    # def _convert_opportunity_data(self, customer, team_id=False):
    #     """ Extract the data from a lead to create the opportunity
    #         :param customer : res.partner record
    #         :param team_id : identifier of the Sales Team to determine the stage
    #     """
    #     new_team_id = team_id if team_id else self.team_id.id
    #     upd_values = {
    #         'type': 'opportunity',
    #         'date_open': fields.Datetime.now(),
    #         'date_conversion': fields.Datetime.now(),
    #     }
    #     if customer != self.partner_id:
    #         upd_values['partner_id'] = customer.id if customer else False
    #     if not self.stage_id:
    #         stage = self._stage_find(team_id=new_team_id)
    #         upd_values['stage_id'] = stage.id
    #     return upd_values

    @api.onchange('opportunity_type_id')
    def onchange_opportunity_type(self):
        for lead in self:
            lead.opportunity_classification_id = False

    def _check_required_bant_fields(self, vals):
        for lead in self:
            if 'budget' in vals:
                budget_ids = vals['budget']
                # Contar los registros eliminados +! y los agregados -1
                delete_count = 0
                for budget_id in budget_ids:
                    if budget_id[0] in (2, 3) and budget_id[2] is False:
                        delete_count += 1
                    else:
                        delete_count -= 1
                if delete_count == len(lead.budget):
                    budget_ids = False
            else:
                budget_ids = lead.budget
            if not budget_ids:
                raise UserError(_('You must select at least one BANT Budget!'))

            if 'authority' in vals:
                authority_ids = vals['authority']

                # Contar los registros eliminados +! y los agregados -1
                delete_count = 0
                for authority_id in authority_ids:
                    if authority_id[0] in (2, 3) and authority_id[2] is False:
                        delete_count += 1
                    else:
                        delete_count -= 1
                if delete_count == len(lead.authority):
                    authority_ids = False
            else:
                authority_ids = lead.authority
            if not authority_ids:
                raise UserError(
                    _('You must select at least one BANT Authority!'))

            if 'need' in vals:
                need = vals['need']
            else:
                need = lead.need
            if not need:
                raise UserError(_('You must select the BANT Need!'))

    # @api.model
    # def create(self, vals):
    #     if 'type' in vals:
    #         type = vals['type']
    #     else:
    #         type = self.type
    #     if type == 'opportunityXXX':
    #         self._check_required_bant_fields(vals)
    #     return super(CrmLead, self).create(vals)

    def write(self, vals):
        if 'type' in vals:
            type = vals['type']
        else:
            type = self.type
        if type == 'opportunity':
            self._check_required_bant_fields(vals)
        return super(CrmLead, self).write(vals)

    @api.depends('bant_score', 'company_id.bant_warning_percentage')
    def compute_bant_score_below_threshold(self):
        for lead in self:
            if lead.bant_score < lead.company_id.bant_warning_percentage:
                lead.bant_score_below_threshold = True
            else:
                lead.bant_score_below_threshold = False

    @api.onchange('need')
    def time_default(self):
        self.time = self.need

    # Método para enviar una Actividad por las Oportunidades que están por debajo del valor deseado
    @api.model
    def action_crm_bant_send_warning(self):
        domain = [
            ("type", "=", "opportunity"),
            ("bant_score_below_threshold", "=", True),
            ("bant_actvity_sent", "=", False), ]
        lead_ids = self.env["crm.lead"].search(domain)
        for lead_id in lead_ids:
            bant_warning_user_ids = lead_id.company_id.bant_warning_user_ids
            bant_warning_percentage = lead_id.company_id.bant_warning_percentage
            try:
                activity_type_id = self.env.ref(
                    "mail.mail_activity_data_todo").id
            except ValueError:
                activity_type_id = False
            # Extraer al jefe directo del "Vendedor"
            employee_id = self.env["hr.employee"].search(
                [('user_id', '=', lead_id.user_id.id)])
            if employee_id and employee_id.parent_id and employee_id.parent_id.user_id:
                bant_warning_user_ids += employee_id.parent_id.user_id
            for user_id in bant_warning_user_ids:
                self.env["mail.activity"].sudo().create(
                    {
                        "activity_type_id": activity_type_id,
                        "summary": _("Opportunity has a BANT Rate below the threshold"),
                        "note": _(
                            "This new opportunity has a BANT Rate below the value %s.\n"
                            "Check if an action is needed." % bant_warning_percentage
                        ),
                        "user_id": user_id.id,
                        "res_id": lead_id.id,
                        "res_model_id": self.env.ref(
                            "crm.model_crm_lead"
                        ).id,
                    }
                )
            lead_id.write({'bant_actvity_sent': True})

    @api.depends('budget', 'authority', 'need')
    def calculo_puntuacion(self):
        for crm_lead_id in self:
            contador_buget = 0
            contador_authority = 0
            total_score = 0
            extra_percent = 0

            for budget in crm_lead_id.budget:
                contador_buget += budget.value
                extra_percent += budget.extra_value
            # Puntos totales de registros en budget
            criterios_budget_total = crm_lead_id.env['criterios.budget'].read_group(
                domain=[], fields=['value:sum'],
                groupby=[], lazy=False)
            budget_total = criterios_budget_total[0]['value']
            if budget_total is not None:
                total_score += (contador_buget /
                                budget_total * 25) + extra_percent

            for rec1 in crm_lead_id.authority:
                contador_authority += rec1.value
            # Puntos totales de registros en authority
            criterios_authority_total = crm_lead_id.env['criterios.authority'].read_group(
                domain=[], fields=['value:sum'],
                groupby=[], lazy=False)
            authority_total = criterios_authority_total[0]['value']
            if authority_total is not None:
                total_score += contador_authority / authority_total * 25

            total_score += int(crm_lead_id.need) + int(crm_lead_id.time)
            crm_lead_id.bant_score = total_score


class CriteriosBudget(models.Model):
    _name = 'criterios.budget'
    _description = 'Criterios Budget'

    name = fields.Char(string="Descripción")
    value = fields.Float(string="Valor", default=1)
    extra_value = fields.Float(string="Porcentaje extra", default=0)


class CriteriosAuthority(models.Model):
    _name = 'criterios.authority'
    _description = 'Criterios Authority'

    name = fields.Char(string="Descripción")
    value = fields.Float(string="Valor", default=1, readonly=True)


class OpportunityType(models.Model):
    _name = 'crm.lead.type'
    _description = 'Opportunity Type'

    name = fields.Char(string="Name", translate=True)
    not_editable = fields.Boolean(
        string="Not Editable", default=False)


class OpportunityClassification(models.Model):
    _name = 'crm.lead.classification'
    _description = 'Opportunity Classification'

    name = fields.Char(string="Name", translate=True)
    opportunity_type_id = fields.Many2one(
        'crm.lead.type',
        string="Opportunity Type",
        help="")
    complexity = fields.Integer(
        string="Complexity", help="")
