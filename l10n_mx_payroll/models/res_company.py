# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta, date


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    
    registro_patronal   = fields.Char('Registro Patronal',
        help="Use esta opción si solo tiene un Registro Patronal")

    registro_patronal_ids = fields.One2many('hr.registro_patronal', 'company_id', string='Registros Patronales')

    factor_riesgo_ids = fields.One2many('hr.riesgo_trabajo', 'company_id', string='Riesgo de Trabajo')
    infonavit_importe_seguro_ids = fields.One2many('hr.infonavit.importe_seguro', 'company_id', 
                                                   string='Infonavit Importe Seguro')

    tipo_calculo_periodo = fields.Selection([
        ('promedio','Días Promedio'),
        ('dias_periodo','Días del Periodo'),
        ], string="Cálculo Nómina", default='dias_periodo', required=True,
        help="Indique la forma en que se manejarán los cálculos en días de la Nómina Quincenal."
             "    - Días Promedio = Se manejan 15.2 días por quincena, o 30.4 por mes"
             "    - Días del Periodo = Se manejan los días por quincena o mes según el periodo,"
             "      Por ejemplo:"
             "          * 1 al 15 de Julio se consideran 15 días"
             "          * 16 al 31 de Julio se consideran 16 días"
             "          * 1 al 15 de Febrero se consideran 15 días"
             "          * 16 al 28 de Febrero se consideran 13 días"
        )

    tipo_calculo_periodo_dias = fields.Float(string="Días a considerar para mes", default="30.4", required=True,
        help="Indique los días a considerar al mes, generalmente son 30.4 pero en algunas empresas consideran 30 días")

    horas_extra_manejo_sueldo_x_hora = fields.Selection([
        ('lft','Según LFT (según Jornada Laboral)'),
        ('8hrs','8 Horas por Turno'),
        ], string="Sueldo x Hora (Horas Extras)", default='lft', required=True)


    horas_extra_tipo_calculo = fields.Selection([
        ('general','General'),
        ('estricto', 'Estricto por Semana')
        ], string="Tipo de Calculo de Horas Extras", default='general', required=True,
        help="Defina cómo desea que se calculen las Horas Extras."
             "General: Calcula el máximo de Horas Extras Dobles según el periodo de la Nómina, y el resto lo determina como Horas Extras Triples."
             "Estricto por Semana: Considera las Horas Extras Dobles de una semana de Lunes a Domingo considerando las siguientes restricciones según la LFT:"
             "    - Máximo 9 Horas Extra Dobles por semana"
             "    - Máximo 3 días a la semana para Horas Extras Dobles, en caso de mas días con Horas Extras serán consideradas Triples"
             "    - Máximo 3 Horas Extras Dobles por día, si hay mas Horas Extras entonces se considerarán Triples"
            )

    horas_extra_dia_inicio_semana = fields.Selection([
        ('6', 'Domingo'),
        ('0', 'Lunes'),
        ('1', 'Martes'),
        ('2', 'Miércoles'),
        ('3', 'Jueves'),
        ('4', 'Viernes'),
        ('5', 'Sábado'),
        ], string="Horas Extras - Inicio de Semana", default='6', required=True,
        help="Indique el día de la semana que considera como 'Inicio de Semana' para el cálculo de Horas Extras Estricto por Semana")

    reglas_salariales_que_incluyen_horas_extras = fields.Many2many(
        'hr.salary.rule', 'company_id_salary_rules_hrs_extras_rel', 'company_id','salary_rule_id',
        string="Reglas Salariales que incluyen Horas Extras",
        domain="[('nomina_aplicacion','=','percepcion')]",
        help="Seleccione las reglas salariales que se pagan por Hora y que incluyen Horas Extras, por consiguiente se tienen que separar las horas del turno de las horas extras."
    ) 

    considerar_descansos_para_premio_puntualidad = fields.Boolean(string="Pagar Premio de Puntualidad para Día de Descanso",
        default=True, help="Si activa entonces se entregará Premio de Puntualidad en días domingo o días de descanso")
    considerar_descansos_para_premio_asistencia = fields.Boolean(string="Pagar Premio de Asistencia para Día de Descanso",
        default=True, help="Si activa entonces se entregará Premio de Puntualidad en días domingo o días de descanso")
    considerar_descansos_para_ayuda_para_transporte = fields.Boolean(string="Considerar descansos para Ayuda para Transporte",
        default=True, help="Si activa entonces se entregará Ayuda para Transporte en días domingo o días de descanso")

    considerar_seguro_de_vida_global = fields.Boolean(string="Considerar los Conceptos de Seguro de Vida, Invalidez y Gastos Médicos Mayores como exentos",
        default=True,
        help="""Para que estos conceptos se consideren exentos, deben de otorgarse a todos los trabajadores, o bien, a todos los Sindicalizados o a todos los No Sindicalizados"""
        )

    version_de_cfdi_para_nominas = fields.Selection(
        [('3.3','CFDI 3.3'),
         ('4.0','CFDI 4.0')],
        string="Versión de CFDI a Usar", default='4.0',
        help="Seleccione cuál es la versión de CFDI que emitirá para Nóminas"
    )
    
    antiguedad_finiquito_proporcionales = fields.Boolean(
        string="Finiquito Antigüedad", default=True,
        help="Active si quiere agregar un día para el cálculo de la Antigüedad"
    )
    
    extras_dentro_de_periodo_de_nomina = fields.Selection(
        [('1', '1- Con Fecha Inicial y Final dentro del Periodo'),
         ('2', '2- Hasta Fecha Final del Periodo')],
        string="Extras de Nómina en Periodo de Nómina",
        help="1- Solo se incluirán los Extras de Nómina con fecha dentro del Periodo de Nómina.\n"
        "2- Se incluyen los Extras de Nómina hasta la Fecha Final del Periodo no incluídos en Nóminas Previas",
        default='1')
    
    antiguedad_finiquito = fields.Selection(
        [('1', 'Fecha Inicio Contrato'),
         ('2', 'Fecha Ingreso')],
        string="Calcular Antigüedad desde:",
        help="Seleccione la forma en que se calcula la Antigüedad del trabajador.\n"
        "Esto aplica al cálculo del Finiquito.",
        default='2')
    antiguedad_segun_lft = fields.Selection(
        [('1', 'Redondear Arriba => (P.Ej: 1.4 = 1 año ó 1.6 = 2.0 año(s)'),
         ('2', 'Redondear Abajo  => (P.Ej: 1.4 = 1 año ó 1.6 = 1.0 año')],
        string="Finiquito - Antigüedad",
        help="Seleccione la forma en que se tomará la Antigüedad del trabajador.\n"
        "Esto aplica al cálculo del Finiquito.",
        default='1')
    
    crear_extra_prima_vacacional_en_aniversario = fields.Selection(
        [('1', 'SI = Crear Extra de Nómina para Prima Vacacional'),
         ('2', 'NO = Pagar Prima cuando disfrute vacaciones')],
        string="Pagar Prima Vacacional en Aniversario",
        default='2')
    
    prima_vacacional_salary_rule_id = fields.Many2one(
        'hr.salary.rule', string="Concepto Prima Vacacional",
        help="Parametro para indicar la Regla Salarial a usarse para generar los Extras de Nómina \n"
        "para la Prima Vacacional a pagar cuando el trabajador cumpla aniversario.\n"
        "Generalmente el concepto es algo parecido a Días de Vacaciones (Prima Vacacional en Aniversario)")
    
    dias_despues_de_aniversario_para_pagar_prima_vacacional = fields.Integer(
        string="Días después de aniversario para pagar Prima Vacacional",
        default=0,
        help="Indique cuantos días, posterior al aniversario, se pagarán los Días por Prima Vacacional"
    )
    
    aplicar_calculo_inverso = fields.Boolean(
        string="Aplicar cálculo inverso",
        default=0,
        help="Parametro para indicar si se debe hacer el cálculo inverso para los conceptos \n"
        "seleccionados. Se sumarán los conceptos y sobre ese monto se recalcularán los \n"
        "montos según su representación porcentual")
    
    reglas_para_calculo_inverso_ids = fields.Many2many(
        'hr.salary.rule', 'company_id_salary_rule_id_rel', 'company_id','salary_rule_id',
        string="Reglas Salariales a aplicar Cálculo Inverso",
        domain="[('nomina_aplicacion','=','percepcion')]",
        help="Seleccione las reglas salariales que se tomarán para aplicar Cálculo Inverso"
    ) 
    
    reprogramar_extras_al_eliminar_de_nomina = fields.Boolean(
        string="Re-Programar Extras de Nómina al quitarlos de una Nómina en Borrador",
        default=True,
        help="Parametro para indicar si en una Nómina en Borrador al eliminar una Entrada \n"
        "(Otras Entradas) ligada a un Extra de Nómina entonces se abra un wizard para \n"
        "re-programar el Extra de Nómina para que no se pierdan.")
    
    dias_para_vencimiento_de_vacaciones = fields.Integer(
        string="Días para vencimiento de Vacaciones",
        default=0,
        help="Indique cuantos días posteriores al vencimiento de las Vacaciones quiere \n"
        "mantenerlas disponibles para el trabajador"
    )
    
    maximo_de_nominas_a_generar_en_batch = fields.Integer(
        string="Número Máximo de Nóminas a Generar en Batch",
        default=0, required=True,
        help="Indique el máximo de Nóminas a Generar cuando se creen desde Lotes de Nóminas\n"
        "Por defecto 0 significa sin límite"
    )
    
    reglas_a_incluir_en_periodo_de_nomina_finiquito_ids = fields.Many2many(
        'hr.salary.rule', 'company_id_salary_rule_id_finiq_rel', 'company_id','salary_rule_id',
        string="Filtrar Reglas Salariales solo en periodo de Nómina (Finiquito)",
        help="""Seleccione las reglas salariales que solo deben tomarse en el periodo de la Nómina (de Finiquito) y descartar cualquier Extra de Nómina posterior al periodo de la Nómina. Esto aplica para conceptos como Fonacot."""
    )
    
    

class HRRegistroPatronal(models.Model):
    _name = 'hr.registro_patronal'
    _description = "Registros Patronales de la Empresa"    
 
    name  = fields.Char('Registro Patronal', required=True)
    notas = fields.Text(string="Notas")
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)

    _sql_constraints = [
        ('company_name_unique', 'unique(company_id, name)','El registro debe ser único')]


class HRRiesgoTrabajo(models.Model):
    _name = 'hr.riesgo_trabajo'
    _description = "Factor de Riesgo de Trabajo"    
    _order = "vigencia desc"

    
    @api.depends('vigencia', 'factor')
    def _compute_name(self):
        for rec in self:
            if rec.vigencia:
                rec.name = _('Vigente desde: ') + rec.vigencia.strftime('%Y-%m-%d') + (_(' - Factor: %s') % rec.factor)
            else:
                rec.name = _('Vigencia sin definir ')
            
    name = fields.Char('Referencia', store=True, compute='_compute_name')
    registro_patronal_id = fields.Many2one('hr.registro_patronal', string="Registro Patronal", required=True)
    factor = fields.Float('Factor', digits=(18,6), required=True, default=0.0)
    vigencia        = fields.Date('Vigencia', required=True)
    notas   = fields.Text(string="Notas")
    company_id          = fields.Many2one('res.company', string='Compañía', required=True,
                                          default=lambda self: self.env.company)

    _sql_constraints = [
        ('company_vigencia_unique', 'unique(company_id, vigencia)','El registro debe ser único')]
    
    

class HRInfonavitImporteSeguro(models.Model):
    _name = 'hr.infonavit.importe_seguro'
    _description = "Infonavit Importe Seguro"    
    _order = "vigencia desc"

    
    @api.depends('vigencia', 'factor')
    def _compute_name(self):
        for rec in self:
            if rec.vigencia:
                rec.name = _(' Vigente desde: ') + rec.vigencia.strftime('%Y-%m-%d') + (_(' - Monto: %s') % rec.factor)
            else:
                rec.name = _('Vigencia sin definir ')
            
    name = fields.Char('Referencia', store=True, compute='_compute_name')
    factor = fields.Float('Monto', digits=(18,6), required=True, default=0.0)
    vigencia        = fields.Date('Vigencia', required=True)
    notas   = fields.Text(string="Notas")
    company_id  = fields.Many2one('res.company', string="Compañía", required=True,
                                  default=lambda self: self.env['res.company']._company_default_get('hr.riesgo_trabajo'))

    _sql_constraints = [
        ('company_vigencia_unique', 'unique(company_id, vigencia)','El registro debe ser único')]    
