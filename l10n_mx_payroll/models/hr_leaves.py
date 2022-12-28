# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.tools.float_utils import float_round
from datetime import datetime, timedelta, date, time
from odoo.osv import expression
import math

from odoo.tools import float_compare, float_is_zero, float_round, date_utils

import logging
_logger = logging.getLogger(__name__)


class HRLeaveGroup(models.Model):
    _name = 'hr.leave.group'
    _description = "Agrupacion para imprimir en Recibo de Nomina"
    
    def name_get(self):
        result = []
        for rec in self:
            name = "["+(rec.code or '')+"] "+(rec.name or '')
            result.append((rec.id, name))
        return result
    
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    
    
    code = fields.Char(string="Código", required=True)
    name = fields.Char(string="Grupo", required=True)
    description = fields.Text(string="Descripción")
    leave_type_ids = fields.One2many('hr.leave.type', 'receipt_group_id',
                                    string="Tipos de Ausencias")
    

    
class HRLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
    hr_salary_rule_id = fields.Many2one('hr.salary.rule', string="Regla Salarial",
                                       help="Si indica una Regla salarial entonces al momento de crear una Ausencia "
                                            "de este tipo también se creará un Extra de Nómina por cada día del Rango "
                                            "de Ausencia")
    es_incapacidad = fields.Boolean(string="Es Incapacidad", index=True, default=False)
    tipoincapacidad_id  = fields.Many2one('sat.nomina.tipoincapacidad', string="·Tipo Incapacidad")
    receipt_group_id = fields.Many2one('hr.leave.group', string="Agrupación",
                                       help="Agrupación a usarse para Recibo de Nomina tipo Nomipaq")
    

    def name_get(self):
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HRLeaveType, self).name_get()
        res = []
        for record in self:
            name = record.name
            if record.requires_allocation == "yes" and not self._context.get('from_manager_leave_form'):
                if record.request_unit == 'hour':
                    name = "%(name)s (%(count)s)" % {
                            'name': name,
                            'count': _('%g restantes de %g') % (
                                float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
                                float_round(record.max_leaves, precision_digits=2) or 0.0,
                            ) + (_(' hours') if record.request_unit == 'hour' else _(' days'))
                        }
                else:
                    employee_id = self._context.get('employee_id')
                    leaves = self.env['hr.leave'].search([
                                ('employee_id', '=', employee_id),
                                ('state', 'in', ['confirm', 'validate1', 'validate']),
                                ('holiday_status_id', '=', record.id)
                            ])
                    dias_usados = sum(leaves.mapped('number_of_days'))
                    name = "%(name)s (%(count)s)" % {
                        'name': name,
                        'count': _('%g restantes de %g ') % (
                            #float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
                            float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
                            float_round(record.max_leaves - dias_usados, precision_digits=2) or 0.0,
                        ) + (_(' hours') if record.request_unit == 'hour' else _(' days'))
                    }
            res.append((record.id, name))
        return res

class HRLeaves(models.Model):
    _inherit = 'hr.leave'


    holiday_status_id = fields.Many2one(
        "hr.leave.type", compute='_compute_from_employee_id', store=True, string="Tipo de Ausencia", required=True, readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]},
        domain=[])

    dias        = fields.Integer(string="Duración del Evento", default=0)
    
    contract_id = fields.Many2one('hr.contract', string="Contrato", readonly=True,
                                  states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    
    date_start  = fields.Date(string="Inicio Periodo", index=True)
    date_end    = fields.Date(string="Final Periodo", index=True)
    vacaciones  = fields.Boolean(string="Son Vacaciones", index=True, 
                                 default=False, readonly=True,
                                 states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    antiguedad  = fields.Integer(string="Antigüedad", required=True, default=0.0, 
                                 copy=False, readonly=True,
                                 states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    
    hr_extra_ids = fields.One2many('hr.payslip.extra', 'leave_id', string="Extras de Nómina", 
                                  readonly=True, 
                                  states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    
    tipoincapacidad_id  = fields.Many2one('sat.nomina.tipoincapacidad', string="·Tipo Incapacidad", 
                                          store=True,
                                          related="holiday_status_id.tipoincapacidad_id", readonly=True)    

    tipoincapacidad_id_code  = fields.Char(related="tipoincapacidad_id.code")
    
    es_incapacidad = fields.Boolean(string="Es Incapacidad", related="holiday_status_id.es_incapacidad",
                                    store=True, readonly=True)    
    #es_continuacion_incapacidad = fields.Boolean(string="Es Continuación de Incapacidad", index=True, 
    #                                             help="Active cuando la ausencia que está registrando es la continuación de una Incapacidad previa. Esto para que siga aplicando el Subsidio por Incapacidad correspondiente.",
    #                                             default=False)
    company_id          = fields.Many2one('res.company', 'Compañía', 
                                          default=lambda self: self.env.company)
    
    num_permiso_horas = fields.Integer(string="# Horas", default=0)
    es_permiso_horas = fields.Boolean(string="Permiso por Horas", default=False)
                                       
    
    @api.onchange('dias','request_date_from')
    def _onchange_dias_request_date_from(self):
        if self.dias:
            self.request_date_to = self.request_date_from + timedelta(days=self.dias-1)                                   
                                       
    
    def action_validate(self):
        res = super(HRLeaves, self).action_validate()
        extra_obj = self.env['hr.payslip.extra']
        for holiday in self.filtered(lambda x: x.holiday_type == 'employee'):
            if holiday.holiday_status_id.hr_salary_rule_id:
                date_from = holiday.date_from
                date_to = holiday.date_to
                data = {'employee_id'       : holiday.employee_id.id,
                        'hr_salary_rule_id' : holiday.holiday_status_id.hr_salary_rule_id.id,
                        'leave_id'        : holiday.id,
                       }
                if holiday.request_unit_hours or holiday.request_unit_half:
                    if not (0.5 <= holiday.number_of_hours_display <= HOURS_PER_DAY):
                        raise ValidationError(_('Advertencia!\n\nLa Ausencia es invalida porque el periodo es menor a media hora y mayor al máximo de %s horas por dia') % HOURS_PER_DAY)
                    
                    data['date'] = date_from.strftime('%Y-%m-%d')
                    extra = extra_obj.new(data)
                    extra.onchange_employee()
                    extra_data = extra._convert_to_write(extra._cache)
                    extra_data['amount'] = extra_data['amount'] / HOURS_PER_DAY * holiday.number_of_hours_display
                    rec = extra_obj.create(extra_data)
                    rec.action_confirm()
                    rec.action_approve()
                else:
                    _logger.info("SI ENTRA !!!")
                    xdias = 0                    
                    for dias in range((date_to - date_from).days+1):
                        fecha = date_from + timedelta(days=dias)
                        #if fecha.weekday() == 6 and not holiday.es_incapacidad: # Domingo, no se toma en cuenta, deberia ?
                        #    xdias += 1
                        #    continue
                        data['date'] = fecha.strftime('%Y-%m-%d')
                        extra = extra_obj.new(data)
                        extra.onchange_employee()
                        extra_data = extra._convert_to_write(extra._cache)
                        if not extra_data.get('contract_id', False):
                            raise ValidationError(_("Advertencia!\nEl Empleado no tiene Contrato válido para la fecha de la Ausencia..."))
                        rec = extra_obj.create(extra_data)
                        rec.action_confirm()
                        rec.action_approve()
            else:
                for extra in holiday.hr_extra_ids:
                    if extra.state=='draft':
                        extra.action_confirm()
                    if extra.state=='confirmed':
                        extra.action_approve()
        return res

    
    def action_refuse(self):
        res = super(HRLeaves, self).action_refuse()        
        for rec in self.filtered(lambda x: x.state=='refuse' and all(w.payslip_state not in ('done','paid') for w in x.hr_extra_ids)):
            rec.hr_extra_ids.action_reject()
            rec.hr_extra_ids.write({'leave_id' : False})
        return res
        

    
    
        
    
