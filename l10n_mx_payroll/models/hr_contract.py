# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta, date
import math
import logging
_logger = logging.getLogger(__name__)


class HRContractLeavesAllocation(models.Model):
    _name = 'hr.contract.leave.allocation'
    _description = 'Asignaciones de Ausencias fijas por Contrato'
    _rec_name = 'holiday_status_id'
    

    contract_id = fields.Many2one('hr.contract', string="Contrato", required=True, index=True, ondelete='cascade')
    holiday_status_id = fields.Many2one(
        "hr.leave.type", string="Tipo de Ausencia", required=True, 
        domain=[('allocation_type', '=', 'fixed')],
        )
    qty      = fields.Integer(string='Cantidad (días)', default=0, required=True)
    accumulative = fields.Boolean(string="Acumulables", default=False)

    notes       = fields.Text(string="Notas")
    
    _sql_constraints = [
        ('contract_id_holiday_status_id', 'unique(contract_id,holiday_status_id)','El Tipo de Ausencia debe ser único'),
        ('check_qty', 'CHECK(qty > 0)',
         'La cantidad debe ser mayor a cero.')
    ]

class HRContractMovimientosPermanentes(models.Model):
    _name = 'hr.contract.movs_permanentes'
    _description = 'Movimientos Permanentes de Empleados hacia Nomina'
    _rec_name = 'hr_salary_rule_id'
    
    contract_id = fields.Many2one('hr.contract', string="Contrato", required=True, index=True)
    hr_salary_rule_id = fields.Many2one('hr.salary.rule', string="Concepto", required=True)
    amount      = fields.Float(string='Monto', digits=(18,4), default=0, required=True)
    move_type = fields.Selection([('fixed','Monto Fijo en Periodo'),
                                  ('fixed_per_day','Monto Diario'),
                                  ('fixed_per_month','Monto Mensual'),
                                  ('percent_on_wage','Porcentaje sobre Sueldo'),
                                  ('percent_on_net','Porcentaje sobre Neto'),
                                  ('python','Código Python')],
                                string="Tipo", default='fixed', required=True
                                )
    
    python_code = fields.Text(string="Código Python")
    
    notes       = fields.Text(string="Notas")
    
    _sql_constraints = [
        ('contract_id_salary_rule_id', 'unique(contract_id,hr_salary_rule_id)','El Concepto para el Movimiento Permanente debe ser único'),
        ('check_amount', 'CHECK(amount > 0)',
         'El monto del Movimiento Permanente debe ser mayor a cero.')
    ]

class HRContractSDI(models.Model):
    _name = 'hr.contract.sdi'
    _description = "Historial de SDIs del contrato / trabajador"
    _order = 'date desc'
    
    contract_id = fields.Many2one('hr.contract', string="Contrato", required=True, index=True, ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', string="Empleado", related='contract_id.employee_id', readonly=True,
                                 store=True)
    date        = fields.Date(string="Fecha", default=fields.Date.context_today, index=True, required=True)
    amount      = fields.Float(string='SBC', digits=(18,4), default=0, required=True)
    notes       = fields.Text(string="Notas")

    _sql_constraints = [
        #('contract_id_date_amount_unique', 'unique(contract_id,date)','El registro del SBC debe ser único en la fecha, ya existe un registro en esta fecha'),
        ('check_amount', 'CHECK(amount > 0)', 'El monto del SBC debe ser mayor a cero.')
    ]


class HRContract(models.Model):
    _inherit = 'hr.contract'
    
    
    
    @api.depends('sdi_ids', 'cfdi_sueldo_base', 'sindicalizado','fecha_ingreso', 'prestacion_id')
    def _get_current_sdi(self):
        dias_aguinaldo = 15
        tabla_vacaciones_obj = self.env['sat.nomina.tabla_vacaciones']
        prestaciones_obj = self.env['sat.nomina.prestaciones']
        for rec in self:
            dias = (fields.Date.context_today(self) - rec.fecha_ingreso).days + 1
            antig_anios = dias / 365.0
            antig_4_vacaciones = math.ceil(antig_anios)
                        
            prest_line = rec.prestacion_id.line_ids.filtered(lambda w: w.antiguedad==antig_4_vacaciones and w.sindicalizado==rec.sindicalizado)
            if prest_line:
                dias_vacaciones = prest_line[0].dias_vacaciones
                prima_vacacional= prest_line[0].prima_vacacional
                dias_aguinaldo  = prest_line[0].dias_aguinaldo
            else:
                vac_line = tabla_vacaciones_obj.search([('antiguedad','=',antig_4_vacaciones)], limit=1)
                dias_vacaciones = vac_line and vac_line.dias or 0
                dias_aguinaldo = 15.0 # Por ley
                prima_vacacional = 25.0 # Por ley
            
            
            monto_aguinaldo = dias_aguinaldo * rec.cfdi_sueldo_base
            monto_prima_vacacional = rec.cfdi_sueldo_base * dias_vacaciones * prima_vacacional / 100.0
            #_logger.info("\nParametros:\ndias_vacaciones: %s\nPrima Vacacional: %s\nDias Aguinaldo: %s\n------------------------\nmonto_aguinaldo: %s\nmonto_prima_vacacional: %s\ncfdi_sueldo_base: %s" % (dias_vacaciones, prima_vacacional, dias_aguinaldo, monto_aguinaldo,monto_prima_vacacional, rec.cfdi_sueldo_base))
            if rec.sdi_ids:
                rec.cfdi_factor_salario_diario_integrado = rec.cfdi_sueldo_base and rec.sdi_ids[0].amount / rec.cfdi_sueldo_base or 0
            else:
                rec.cfdi_factor_salario_diario_integrado = rec.cfdi_sueldo_base and \
                                                        (((rec.cfdi_sueldo_base * 365.0) + monto_aguinaldo + monto_prima_vacacional) / (rec.cfdi_sueldo_base * 365.0)) or 0
                
            # Variables 
            variables = 0.0
            uma = self.env['sat.nomina.uma_umi'].search([('tipo','=','uma')], order='vigencia desc', limit=1)
            # Vales de Despensa
            if rec.prestacion_vales_despensa:
                monto_exento = uma.monto * 0.4
                if rec.prestacion_vales_despensa > monto_exento:
                    if rec.company_id.tipo_calculo_periodo=='promedio': # 30.4
                        monto_exento_mensual = monto_exento * 30.4
                        monto_vales_despensa = round(rec.prestacion_vales_despensa * rec.company_id.tipo_calculo_periodo_dias, 0)
                        monto_gravado_mensual = monto_vales_despensa - monto_exento_mensual
                        variables += round(monto_gravado_mensual / rec.company_id.tipo_calculo_periodo_dias, 2)
                    else:
                        variables += rec.prestacion_vales_despensa - monto_exento
            # Fondo de Ahorro
            if rec.prestacion_fondo_ahorro:
                monto_exento = uma.monto * 1.3
                monto_fondo_ahorro = rec.cfdi_sueldo_base * (rec.prestacion_fondo_ahorro / 100.0)
                if monto_fondo_ahorro > monto_exento:
                    if rec.company_id.tipo_calculo_periodo=='promedio': # 30.4
                        monto_exento_mensual = monto_exento * 30.4
                        monto_fondo_ahorro = round(monto_fondo_ahorro * rec.company_id.tipo_calculo_periodo_dias, 0)
                        monto_gravado_mensual = monto_vales_despensa - monto_exento_mensual
                        variables += round(monto_gravado_mensual / rec.company_id.tipo_calculo_periodo_dias, 2)
                    else:
                        variables += monto_fondo_ahorro - monto_exento

            # Fin Variables
            rec.cfdi_salario_diario_integrado_variables = variables
            rec.cfdi_salario_diario_preintegrado = rec.cfdi_sueldo_base  and \
                                                ((((rec.cfdi_sueldo_base * 365.0) + monto_aguinaldo + monto_prima_vacacional) / 365.0)) or 0
            rec.cfdi_salario_diario_integrado = rec.cfdi_sueldo_base  and \
                                                        ((((rec.cfdi_sueldo_base * 365.0) + monto_aguinaldo + monto_prima_vacacional) / 365.0)+variables) or 0
            rec.cfdi_salario_diario_integrado2 = rec.sdi_ids and rec.sdi_ids[0].amount or rec.cfdi_salario_diario_integrado
            #rec.cfdi_factor_salario_diario_integrado = rec.cfdi_sueldo_base and (rec.cfdi_salario_diario_integrado2 / rec.cfdi_sueldo_base) or 0

            try:
                rec.cfdi_sueldo_base_con_prevision = eval(rec.calculo_prevision_social % rec.cfdi_sueldo_base)
                rec.cfdi_sueldo_base_con_prevision_gravada = eval(rec.calculo_prevision_social_gravada % rec.cfdi_sueldo_base)
            except:
                rec.cfdi_sueldo_base_con_prevision = rec.cfdi_sueldo_base
                rec.cfdi_sueldo_base_con_prevision_gravada = rec.cfdi_sueldo_base
            
    
    
    @api.depends('date_start')
    def _compute_contract_data(self):
        for rec in self:
            #rec.cfdi_salario_diario_integrado = rec.cfdi_factor_salario_diario_integrado * rec.cfdi_sueldo_base
            rec.sat_antiguedad = 'P2Y4M12D' # TODO
            
    @api.depends('structure_type_id')
    def _get_tipo_sueldo(self):
        for rec in self:
            if not rec.structure_type_id:
                rec.tipo_sueldo= 'diario'
            else:
                rec.tipo_sueldo = rec.structure_type_id.wage_type=='monthly' and 'diario' or 'hora'
    
    resource_calendar_id = fields.Many2one(
        'resource.calendar', 'Horario de Trabajo',
        default=lambda self: self.env.company.resource_calendar_id.id, copy=True, index=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", 
        readonly=True, states={'draft': [('readonly', False)]})

    prestaciones = fields.Text(string="Prestaciones")
    is_template = fields.Boolean(string="Es Plantilla", default=False, index=True)
    
    state = fields.Selection(selection_add=[('baja', 'Baja')])
    
    struct_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial', 
                                tracking=True, required=False) 
    job_id = fields.Many2one('hr.job', tracking=True, copy=True,
                              readonly=True, states={'draft': [('readonly', False)]})
    
    department_id = fields.Many2one('hr.department', tracking=True, copy=True,
                                     readonly=True, states={'draft': [('readonly', False)]})
    

    date_start = fields.Date('Start Date', required=True, default=fields.Date.today,
                            tracking=True, help="Start date of the contract.", 
                            readonly=True, states={'draft': [('readonly', False)]})
    date_end = fields.Date('End Date',
                            tracking=True, help="End date of the contract (if it's a fixed-term contract).", 
                            readonly=True, states={'draft': [('readonly', False)]})
    
    fecha_ingreso = fields.Date(string="Fecha Ingreso", default=fields.Date.context_today, 
                                tracking=True, index=True, required=True,
                                help="Use esta fecha para definir la Fecha de Ingreso del Trabajador para cuestiones de Antigüedad", 
                                readonly=True, states={'draft': [('readonly', False)]})
    
    movs_permanentes_ids = fields.One2many('hr.contract.movs_permanentes', 'contract_id', copy=True,
                                           string="Movimientos Permanentes")
    
    leave_allocation_ids = fields.One2many('hr.contract.leave.allocation', 'contract_id', copy=True,
        string="Ausencias Asignadas Anualmente", 
        readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    sdi_ids = fields.One2many('hr.contract.sdi', 'contract_id', string="SDIs", copy=False)
    sat_antiguedad = fields.Char('Antigüedad', compute="_compute_contract_data")
    sat_tipo_contrato_id = fields.Many2one('sat.nomina.tipocontrato', string="SAT Tipo Contrato", 
                                           required=False, tracking=True)

    calculo_prevision_social = fields.Char(string="Prev. Social", required=True, 
        help="Indique la fórmula para calcular el Sueldo con Previsión Social\n"
             "Ej. (%s * 1.1 + 125.92) => Esto aplicaría cuando entrega un bono de puntualidad del 10% y Vale de Despensa diario de 125.92)",
        tracking=True, default='%s', 
        readonly=True, states={'draft': [('readonly', False)]})

    calculo_prevision_social_gravada = fields.Char(string="Prev Social Gravada", required=True, 
        help="Indique la fórmula para calcular el Sueldo con Previsión Social Gravado\n"
             "Ej. (%s * 1.1) => Esto aplicaría cuando entrega un bono de puntualidad del 10%)",
        tracking=True, default='%s', 
        readonly=True, states={'draft': [('readonly', False)]})
    
    sat_periodicidadpago_id = fields.Many2one('sat.nomina.periodicidadpago', string="Periodicidad Pago",
                                             tracking=True, required=False, 
        readonly=True, states={'draft': [('readonly', False)]})
    sat_tipojornada_id = fields.Many2one('sat.nomina.tipojornada', string="Jornada Laboral",
                                        tracking=True, required=False, 
        readonly=True, states={'draft': [('readonly', False)]})
    sat_tiporegimen_id = fields.Many2one('sat.nomina.tiporegimen', string="Regimen Laboral",
                                        tracking=True, required=False, 
        readonly=True, states={'draft': [('readonly', False)]})
    sat_riesgopuesto_id      = fields.Many2one('sat.nomina.riesgopuesto', 'Tipo Riesgo Puesto',
                                               tracking=True, required=False,
                                               help="Catálogo de clases de Riesgo en que deben inscribirse los patrones.", 
        readonly=True, states={'draft': [('readonly', False)]})
    # hr.settlement    
    cfdi_sueldo_base_con_prevision = fields.Float('Sueldo con Previsión Social', digits=(18,4), 
                                                  compute="_get_current_sdi", compute_sudo=True)

    cfdi_sueldo_base_con_prevision_gravada = fields.Float('Sueldo + Previsión Social (Grav)', digits=(18,4), 
        compute="_get_current_sdi", compute_sudo=True)
    
    cfdi_sueldo_base = fields.Float('Sueldo', digits=(18,4), default=0,
                                    tracking=True, required=True,
                                    help="""Salario diario registrado ante el IMSS. Este se toma como\n"""
                                         """base para los cálculos de Percepciones y Deducciones\n"""
                                         """Puede ser Diario, por Hora, o según corresponda.""", 
        readonly=True, states={'draft': [('readonly', False)]})
    cfdi_factor_salario_diario_integrado = fields.Float(string='Factor SDI', digits=(18,6), #default=1.0452,
                                                        tracking=True,
                                                        compute='_get_current_sdi', compute_sudo=True,
                                                        help="Factor para cálculo de Salario Diario Integrado")
    
    cfdi_salario_diario_integrado = fields.Float(string='SDI', digits=(18,2), default=0, store=True,
                                                help="Salario Diario Integrado",
                                                compute="_get_current_sdi", compute_sudo=True)

    cfdi_salario_diario_preintegrado = fields.Float(string='SDI Pre-Integrado', digits=(18,2), default=0, store=True,
        help="Salario Diario Pre-Integrado", compute="_get_current_sdi", compute_sudo=True)

    cfdi_salario_diario_integrado_variables = fields.Float(string='SDI Variables', digits=(18,2), default=0, store=True,
        help="SDI Variables", compute="_get_current_sdi", compute_sudo=True)

    cfdi_salario_diario_integrado2 = fields.Float('SBC', digits=(18,2), store=True,
                                                  compute="_get_current_sdi", tracking=True,
                                                  compute_sudo=True,
                                                  help="""Salario Base de Cotización usado para cálculos del IMSS.""")
    wage_type = fields.Selection(related="structure_type_id.wage_type", readonly=True)
    tipo_sueldo = fields.Selection([('hora','Por Hora'),
                                    ('diario','Diario')],
                                  string="Tipo Salario", compute="_get_tipo_sueldo")
    
    dias_aguinaldo = fields.Integer(string="Días para Aguinaldo", default=15,
                                    tracking=True,
                                    help="Días que se usarán para calcular el Salario Diario Integrado\n"
                                         "y el Aguinaldo en Diciembre", 
        readonly=True, states={'draft': [('readonly', False)]})
    
    dias_vacaciones = fields.Integer(string="Días Vacaciones", 
                                     tracking=True,
                                     help="Días que se usarán para calcular el Salario Diario Integrado\n"
                                          "y el Aguinaldo en Diciembre", 
        readonly=True, states={'draft': [('readonly', False)]})
    
    prima_vacacional= fields.Float(string="Prima Vacacional", default=25.0,
                                   tracking=True,
                                   help="Porcentaje a usar como Prima Vacacional, por ley mínimo es 25%", 
        readonly=True, states={'draft': [('readonly', False)]})
    
    sindicalizado = fields.Selection([('Si','Sindicalizado'),
                                      ('No','De Confianza')],
                                     tracking=True,
                                     string="Sindicalizado", default='No', 
        readonly=True, states={'draft': [('readonly', False)]})

    leave_ids = fields.One2many('hr.leave', 'contract_id', string="Ausencias relacionadas")
    
    #company_id = fields.Many2one('res.company', string='Compañía', 
    #                                      default=lambda self: self.env['res.company']._company_default_get('hr.contract'))
    
    tipo_salario_minimo = fields.Selection([
        ('smg', 'Salario Mínimo General'),
        ('smfn', 'Salario Mínimo Frontera Norte'), 
        ], string="Zona Salario Mínimo", tracking=True, required=True, default='smg', 
        readonly=True, states={'draft': [('readonly', False)]})

    # Prestaciones

    prestacion_premio_puntualidad = fields.Float(string="Premio x Puntualidad", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el Premio por Puntualidad (Por ejemplo: 10.00 para referirse a 10%)",
        tracking=True, default=0, 
        readonly=True, states={'draft': [('readonly', False)]})
    prestacion_premio_asistencia  = fields.Float(string="Premio x Asistencia", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el Premio por Asistencia (Por ejemplo: 10.00 para referirse a 10%)",
        tracking=True, default=0, 
        readonly=True, states={'draft': [('readonly', False)]})
    prestacion_vales_despensa  = fields.Float(string="Vales de Despensa", digits=(10,4), default=0, required=True,
        help="Indique el monto diario para Vales de Despensa", tracking=True, 
        readonly=True, states={'draft': [('readonly', False)]})
    prestacion_fondo_ahorro    = fields.Float(string="Fondo de Ahorro", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el concepto de Fondo de Ahorro (Por ejemplo: 5.00 para referirse a 5%)",
        tracking=True, default=0, 
        readonly=True, states={'draft': [('readonly', False)]})
    prestacion_caja_ahorro    = fields.Float(string="Caja de Ahorro", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el concepto de Caja de Ahorro (Por ejemplo: 7.5 para referirse a 7.5%)",
        tracking=True, default=0, 
        readonly=True, states={'draft': [('readonly', False)]})
    prestacion_subsidio_por_incapacidad = fields.Boolean(string="Aplicar Subsidio por Incapacidad", 
        help="Active si el trabajador tendrá la prestación de Subsidio por incapacidad, esto es, cuando el trabajador tenga incapacidad.",
        tracking=True, required=False,
        readonly=True, states={'draft': [('readonly', False)]})

    prestacion_id = fields.Many2one('sat.nomina.prestaciones', string="Prestación Adicional a la Ley",
        tracking=True, 
        readonly=True, states={'draft': [('readonly', False)]})

    registro_patronal_id = fields.Many2one('hr.registro_patronal', string="Registro Patronal", required=True, index=True, 
        readonly=True, states={'draft': [('readonly', False)]})

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        contracts = self.filtered(lambda c: c.date_end and c.date_start > c.date_end)
        if contracts:
            contratos = []
            for c in contracts:
                contratos.append("Contrato:  %s - %s - Fecha Inicial: %s - Fecha Final: %s" % (c.id, c.name, c.date_start, c.date_end))
            if contratos:
                raise ValidationError(_('La Fecha Inicial no debe ser mayor a la Fecha Final. Revise los siguientes contratos:\n%s' % '\n'.join(contratos)))
            #raise ValidationError(_('La Contract start date must be earlier than contract end date.'))
            
    @api.constrains('prima_vacacional')
    def _check_prima_vacacional(self):
        if self.filtered(lambda c: c.prima_vacacional < 25):
            raise ValidationError(_('El Porcentaje de Prima Vacacional no puede ser menor a 25%.'))
            
    @api.onchange('prestacion_id')
    def _onchange_prestacion_id(self):
        if self.prestacion_id:
            self.prestacion_premio_puntualidad = self.prestacion_id.prestacion_premio_puntualidad
            self.prestacion_premio_asistencia = self.prestacion_id.prestacion_premio_asistencia
            self.prestacion_vales_despensa = self.prestacion_id.prestacion_vales_despensa
            self.prestacion_fondo_ahorro = self.prestacion_id.prestacion_fondo_ahorro
            self.prestacion_caja_ahorro = self.prestacion_id.prestacion_caja_ahorro
            self.prestacion_subsidio_por_incapacidad = self.prestacion_id.prestacion_subsidio_por_incapacidad
        else:
            self.prestacion_premio_puntualidad = 0
            self.prestacion_premio_asistencia = 0
            self.prestacion_vales_despensa = 0
            self.prestacion_fondo_ahorro = 0
            self.prestacion_caja_ahorro = 0
            self.prestacion_subsidio_por_incapacidad = False


    @api.onchange('cfdi_sueldo_base','prestacion_premio_puntualidad','prestacion_premio_asistencia', 'prestacion_vales_despensa')
    def _onchange_prestaciones(self):
        if self.prestacion_premio_puntualidad > 10.00:
            raise ValidationError(_("No puede manejar un monto mayor al 10% por el Concepto de Premio por Puntualidad"))
        if self.prestacion_premio_asistencia > 10.00:
            raise ValidationError(_("No puede manejar un monto mayor al 10% por el Concepto de Premio por Asistencia")) 
        self.calculo_prevision_social = '%s * %s + %s' % ('%s', '{:.2f}'.format(1.0 + ((self.prestacion_premio_puntualidad + self.prestacion_premio_asistencia) / 100.00)), '{:.2f}'.format(self.prestacion_vales_despensa))
        self.calculo_prevision_social_gravada  = '%s * %s' % ('%s', '{:.2f}'.format(1.0 + ((self.prestacion_premio_puntualidad + self.prestacion_premio_asistencia) / 100.00)))

    @api.onchange('schedule_pay')
    def _onchange_schedule_pay(self):
        if self.schedule_pay:
            data = {'dayly'     : '01', 'weekly'    : '02', 'two-weeks' : '03',
                    'bi-weekly' : '04', 'monthly'   : '05', 'bi-monthly': '06',
                    'piecework' : '07', 'commission': '08', 'priceraised': '09',
                    'ten-days'  : '10', 'other'     : '99',
                   }
            res = self.env['sat.nomina.periodicidadpago'].search([('code','=',data[self.schedule_pay])], limit=1)
            self.sat_periodicidadpago_id = res.id
        else:
            self.sat_periodicidadpago_id = False
    
    def _faltas_periodo_anual(self, fecha):
        self.ensure_one()
        reglas = self.env['hr.salary.rule'].search([('category_id.code','in',('FALTAS','FALTAS_SIN_GOCE','INCAP_ENFERMEDAD_GENERAL'))])
        faltas = self.env['hr.payslip.extra'].search([('employee_id','=',self.employee_id.id),
                                                      ('state','=','done'),
                                                      ('date','>=', date(fecha.year,1,1)),
                                                      ('hr_salary_rule_id', 'in', reglas.ids)]) 
        return sum(faltas.mapped('qty'))

    @api.model
    def create(self, vals):
        contracts = super(HRContract, self).create(vals)
        if vals.get('department_id', False) or vals.get('job_id', False) or vals.get('resource_calendar_id', False):
            for rec in contracts:
                rec.employee_id.write({
                    'department_id' : rec.department_id.id,
                    'job_id'        : rec.job_id.id,
                    'resource_calendar_id' : rec.resource_calendar_id.id,
                    })
        return contracts
    
    def write(self, vals):
        contratos = []
        for rec in self:
            if 'cfdi_sueldo_base' in vals and round(rec.cfdi_sueldo_base,2) != round(vals['cfdi_sueldo_base'],2) and \
               'state' not in vals and rec.state in ('open','draft') and rec.cfdi_salario_diario_integrado2:
                contratos.append({'contract_id' : rec.id, 
                                  'variable' : rec.cfdi_salario_diario_integrado2 - rec.cfdi_salario_diario_integrado})
            if vals.get('department_id', False) or vals.get('job_id', False) or vals.get('resource_calendar_id', False):
                rec.employee_id.write({
                    'department_id' : rec.department_id.id,
                    'job_id'        : rec.job_id.id,
                    'resource_calendar_id' : rec.resource_calendar_id.id,
                    })    

        res = super(HRContract, self).write(vals)
        
        if contratos:
            contract_obj = self.env['hr.contract']
            sdi_obj = self.env['hr.contract.sdi']
            for c in contratos:
                #_logger.info("c: %s" % (c))
                contrato = contract_obj.browse(c['contract_id'])
                sdi = contrato.cfdi_salario_diario_integrado + c['variable']
                xres = sdi_obj.create({'contract_id' : c['contract_id'],
                        'amount'      : sdi,
                        'notes'       : _('Modificación de Salario')})
        return res
