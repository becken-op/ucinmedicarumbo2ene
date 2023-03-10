# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    registro_patronal = fields.Char('Registro Patronal',
                                    related="company_id.registro_patronal", readonly=False,
                                    help="Capture el Registro Patronal entregado por el IMSS sin guiones ni espacios")

    registro_patronal_ids = fields.One2many(related="company_id.registro_patronal_ids", readonly=False)
    factor_riesgo_ids = fields.One2many(related="company_id.factor_riesgo_ids", readonly=False)
    infonavit_importe_seguro_ids = fields.One2many(related="company_id.infonavit_importe_seguro_ids", readonly=False)


    tipo_calculo_periodo = fields.Selection(related="company_id.tipo_calculo_periodo", readonly=False) 

    tipo_calculo_periodo_dias = fields.Float(related="company_id.tipo_calculo_periodo_dias", readonly=False)
    
    horas_extra_manejo_sueldo_x_hora = fields.Selection(related="company_id.horas_extra_manejo_sueldo_x_hora", readonly=False)
    horas_extra_tipo_calculo = fields.Selection(related="company_id.horas_extra_tipo_calculo", readonly=False)
    horas_extra_dia_inicio_semana = fields.Selection(related="company_id.horas_extra_dia_inicio_semana", readonly=False)    
    reglas_salariales_que_incluyen_horas_extras = fields.Many2many(
        related="company_id.reglas_salariales_que_incluyen_horas_extras", readonly=False)

    
    considerar_descansos_para_premio_puntualidad = fields.Boolean(related="company_id.considerar_descansos_para_premio_puntualidad", readonly=False)
    considerar_descansos_para_premio_asistencia = fields.Boolean(related="company_id.considerar_descansos_para_premio_asistencia", readonly=False)
    considerar_descansos_para_ayuda_para_transporte = fields.Boolean(related="company_id.considerar_descansos_para_ayuda_para_transporte", readonly=False)
    considerar_seguro_de_vida_global = fields.Boolean(related="company_id.considerar_seguro_de_vida_global", readonly=False)
    
    version_de_cfdi_para_nominas = fields.Selection(related="company_id.version_de_cfdi_para_nominas", readonly=False)
    
    antiguedad_finiquito_proporcionales = fields.Boolean(
        related="company_id.antiguedad_finiquito_proporcionales", readonly=False)
    
    extras_dentro_de_periodo_de_nomina = fields.Selection(
        related="company_id.extras_dentro_de_periodo_de_nomina", readonly=False)
    
    antiguedad_finiquito = fields.Selection(
        related="company_id.antiguedad_finiquito", readonly=False)
    
    antiguedad_segun_lft = fields.Selection(
        related="company_id.antiguedad_segun_lft", readonly=False)
    
    crear_extra_prima_vacacional_en_aniversario = fields.Selection(
        related="company_id.crear_extra_prima_vacacional_en_aniversario", readonly=False)
    
    prima_vacacional_salary_rule_id = fields.Many2one(
        'hr.salary.rule', string="Concepto Prima Vacacional",
        related="company_id.prima_vacacional_salary_rule_id", readonly=False)

    dias_despues_de_aniversario_para_pagar_prima_vacacional = fields.Integer(
        string="D??as despu??s de aniversario para pagar Prima Vacacional",
        related="company_id.dias_despues_de_aniversario_para_pagar_prima_vacacional", readonly=False,
        help="Indique cuantos d??as, posterior al aniversario, se pagar??n los D??as por Prima Vacacional")
    
    aplicar_calculo_inverso = fields.Boolean(
        string="Aplicar c??lculo inverso",
        related="company_id.aplicar_calculo_inverso", readonly=False,
        help="Parametro para indicar si se debe hacer el c??lculo inverso para los conceptos \n"
        "seleccionados. Se sumar??n los conceptos y sobre ese monto se recalcular??n los \n"
        "montos seg??n su representaci??n porcentual")
    
    reglas_para_calculo_inverso_ids = fields.Many2many(
        string="Reglas Salariales a aplicar C??lculo Inverso",
        related="company_id.reglas_para_calculo_inverso_ids", readonly=False,
        help="Seleccione las reglas salariales que se tomar??n para aplicar C??lculo Inverso"
    )
    
    reprogramar_extras_al_eliminar_de_nomina = fields.Boolean(
        string="Re-Programar Extras de N??mina al quitarlos de una N??mina en Borrador",
        related="company_id.reprogramar_extras_al_eliminar_de_nomina", readonly=False,
        help="Parametro para indicar si en una N??mina en Borrador al eliminar una Entrada \n"
        "(Otras Entradas) ligada a un Extra de N??mina entonces se abra un wizard para \n"
        "re-programar el Extra de N??mina para que no se pierdan.")

    dias_para_vencimiento_de_vacaciones = fields.Integer(
        string="D??as para vencimiento de Vacaciones",
        related="company_id.dias_para_vencimiento_de_vacaciones", readonly=False,
        help="Indique cuantos d??as posteriores al vencimiento de las Vacaciones  quiere \n"
        "mantenerlas disponibles para el trabajador"
    )
    
    maximo_de_nominas_a_generar_en_batch = fields.Integer(
        string="N??mero M??ximo de N??minas a Generar en Batch",
        related="company_id.maximo_de_nominas_a_generar_en_batch", readonly=False,
        help="Indique el m??ximo de N??minas a Generar cuando se creen desde Lotes de N??minas\n"
        "Por defecto 0 significa sin l??mite"
    )
    
    reglas_a_incluir_en_periodo_de_nomina_finiquito_ids = fields.Many2many(
        related="company_id.reglas_a_incluir_en_periodo_de_nomina_finiquito_ids", readonly=False,
    )
    