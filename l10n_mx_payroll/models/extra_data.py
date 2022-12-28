# -*- encoding: utf-8 -*-
##############################################################################

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import expression

import logging
_logger = logging.getLogger(__name__)



##### Tabla Causas de Terminación de Relación Laboral
class HRPayroll_CausaTerminacionRelacionLaboral(models.Model):
    _name = 'hr.causa_fin_relacion_laboral'
    _description = 'Causas de Terminacion de Relacion Laboral'

    code = fields.Char('Código', required=True)
    name = fields.Char('Causa supuesta', required=True)
    
    indemnizacion_90_dias = fields.Boolean(string="Indemnización (90 días)")
    indemnizacion_20_dias = fields.Boolean(string="Indemnización (20 días x año)")
    prima_antiguedad_12_dias = fields.Boolean(string="Prima Antigüedad (12 días x año)")
    prima_antiguedad_15_anios = fields.Boolean(string="Prima de Antigüedad (Antig. >= 15 años)")
    gratif_x_invalidez = fields.Boolean(string="Gratificación por Invalidez")
    salarios_vencidos = fields.Boolean(string="Salarios Vencidos")
    type        = fields.Selection([('finiquito','Finiquito'),
                                    ('liquidacion','Liquidación')],
                                  string="Tipo", required=True, default='finiquito')
    active = fields.Boolean(string="Activo", default="True")

    _sql_constraints = [
        ('name_unique', 'unique(name)','El registro debe ser único'),
        ('code_unique', 'unique(code)','El registro debe ser único')]
    
        
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
    

######### CARGA DE CATALOGOS DEL SAT PARA NOMINAS ############

##### Tabla Factores IMSS
class HRPayroll_TablaFactoresIMSS(models.Model):
    _name = 'sat.nomina.factores_imss'
    _description = 'SAT - Primas por ramo de Seguro.'
    _order = "vigencia desc"

    
    api.depends('vigencia', 'tipo_seguro', 'prestacion', 'tipo_cuota')
    def _compute_name(self):
        for rec in self:
            rec.name = '/'
            if rec.vigencia and rec.tipo_seguro and rec.prestacion:
                rec.name = _('%s - %s - Vigente desde: %s') % (
                            dict(rec._fields['tipo_seguro'].selection).get(rec.tipo_seguro), 
                            (rec.tipo_seguro == 'enfermedades_y_maternidad' and \
                              dict(rec._fields['tipo_cuota'].selection).get(rec.tipo_cuota)  or ''),
                            rec.vigencia.strftime('%Y-%m-%d'))
            
                
    @api.depends('cuota_trabajador', 'cuota_patron')
    def _compute_cuota(self):
        for rec in self:
            rec.cuota_total = rec.cuota_trabajador + rec.cuota_patron
            
            
                
    name = fields.Char(string='Concepto', store=True, compute='_compute_name')
    sequence = fields.Integer(default=10)
    
    tipo_seguro      = fields.Selection([
                                         ('enf_y_mat_en_especie_cuota_fija','Enfermedades y Maternidad (En Especie - Cuota Fija)'),
                                         ('enf_y_mat_en_especie_cuota_adicional','Enfermedades y Maternidad (En Especie - Cuota Adicional)'),
                                         ('enf_y_mat_en_gts_medicos','Enfermedades y Maternidad (Gastos médicos para pensionados y beneficiarios)'),
                                         ('enf_y_mat_en_dinero','Enfermedades y Maternidad (En Dinero)'),
                                         ('invalidez_y_vida','Invalidez y Vida (En especie y dinero)'),
                                         ('ceav_retiro','Retiro, Cesantía en Edad Avanzada y Vejez (Retiro)'),
                                         ('ceav_ceav','Retiro, Cesantía en Edad Avanzada y Vejez (CEAV)'),
                                         ('prestaciones_sociales','Guarderías y Prestaciones Sociales (En Especie)'),
                                         ('infonavit','Infonavit (Crédito de Vivienda)'),
                                         ],
                                      string="Tipo Prima de Seguro", required=True)
    
    
    
    cuota_patron        = fields.Float('Cuota Patrón %', digits=(18,3), required=True, default=0.0)
    cuota_trabajador    = fields.Float('Cuota Trabajador %', digits=(18,3), required=True, default=0.0)
    cuota_total         = fields.Float('Cuota Total %', digits=(18,3), compute="_compute_cuota")
    
    """
    base_calculo_patron = fields.Char(string="Base Cálculo Patrón")
    base_calculo_trabajador = fields.Selection([('uma','UMA'),
                                                ('sbc', 'Salario Base de Cotización'),
                                                ('diff_sbc_3_uma' , 'Diferencia entre el SBC y tres veces la UMA')],
                                              string="Base Cálculo Trabajador", required=True)
    """
    vigencia        = fields.Date('Vigencia', required=True)

    _sql_constraints = [
        ('vigencia_tipo_seguro_unique', 'unique(vigencia,tipo_seguro)','El registro debe ser único')]


##### Tabla Salario Minimo
class HRPayroll_TablaSalarioMinimo(models.Model):
    _name = 'sat.nomina.salario_minimo'
    _description = 'SAT - Salario Mínimo.'
    _order = "vigencia"

    
    @api.depends('tipo','vigencia', 'monto')
    def _compute_name(self):
        for rec in self:
            if rec.vigencia and rec.monto:
                rec.name =  (_('SM - ') if rec.tipo=='smg' else _('SMFN - '))  + str(rec.monto) + _(' - Desde: ') + rec.vigencia.strftime('%Y-%m-%d')
            else:
                rec.name = '/'
                
    name = fields.Char('Descripción', store=True, compute='_compute_name')
    tipo        = fields.Selection([('smg', 'Salario Mínimo General'),
                                    ('smfn', 'Salario Mínimo Frontera Norte'),
                                   ], string="Tipo", required=True, default='smg')
    monto            = fields.Float('Monto', digits=(18,2), required=True)
    vigencia        = fields.Date('Vigencia', required=True)

    _sql_constraints = [
        ('vigencia_unique', 'unique(tipo, vigencia)','La vigencia debe ser única')]



##### Tabla UMA
class HRPayroll_Tabla_UMA_UMI(models.Model):
    _name = 'sat.nomina.uma_umi'
    _description = 'SAT - UMA y UMI'
    _order = "vigencia"

    @api.depends('tipo','vigencia', 'monto')
    def _compute_name(self):
        for rec in self:
            if rec.vigencia and rec.monto:
                rec.name = ('UMA - ' if rec.tipo=='uma' else 'UMI - ') + str(rec.monto) + _(' - Desde: ') + rec.vigencia.strftime('%Y-%m-%d')
            else:
                rec.name = '/'
                
    name        = fields.Char('Descripción', store=True, compute='_compute_name')
    tipo        = fields.Selection([('uma', 'UMA'),
                                    ('umi', 'UMI'),
                                   ], string="Tipo", required=True)
    monto       = fields.Float('Monto', digits=(18,2), required=True)
    vigencia    = fields.Date('Vigencia', required=True)
    
    
    _sql_constraints = [
        ('vigencia_unique', 'unique(tipo, vigencia)','El Tipo y la Vigencia deben ser únicos')]
    
##### Tabla Art 113 LISR
class HRPayroll_TablaISR(models.Model):
    _name = 'sat.nomina.tabla_isr'
    _description = 'SAT - Tabla Art. 113 Ley ISR.'
    _order = "sequence, tipo, vigencia, limite_inferior"
    
    @api.depends('tipo')
    def _compute_seq(self):
        seq = {'diaria'     : 10,
               'semanal'    : 20,
               'decenal'    : 30,
               'quincenal'  : 40,
               'mensual'    : 50,
               'anual'      : 60,
              }
        for rec in self:
            rec.sequence = seq[rec.tipo]
    
    @api.depends('tipo','vigencia', 'limite_inferior', 'limite_superior')
    def _compute_name(self):
        for rec in self:
            if rec.vigencia and rec.limite_inferior and rec.limite_superior:
                val = dict(rec.fields_get(allfields=['tipo'])['tipo']['selection'])[rec.tipo]
                rec.name = 'Para Nómina: ' + val + ' - ' + rec.vigencia.strftime('%Y-%m-%d') + _(' - Límite Inf: ') + str(rec.limite_inferior) + _(' - Límite Sup: ') + str(rec.limite_superior)
            else:
                rec.name = '/'
    
    name = fields.Char('Descripción', store=True, compute='_compute_name')
    limite_inferior = fields.Float('Límite Inferior', digits=(18,2), required=True, index=True)
    limite_superior = fields.Float('Límite Superior', digits=(18,2), required=True, index=True)
    cuota_fija      = fields.Float('Cuota Fija', digits=(18,2), required=True)
    tasa            = fields.Float('Tasa (%)', digits=(18,2), required=True)
    vigencia        = fields.Date('Vigencia', required=True)
    tipo            = fields.Selection([('diaria', ' Diaria'),
                                        ('semanal', '  Semanal'),
                                        ('decenal', '   Decenal'),
                                        ('quincenal', '  Quincenal'),
                                        ('mensual', ' Mensual'),
                                        ('anual', '   Anual'),
                                       ], string="Aplica a Nómina", default='quincenal', required=True)
    sequence        = fields.Integer(string="Sec", compute="_compute_seq", store=True)
    
##### Tabla Subsidio al Empleo
class HRPayroll_TablaSubsidioEmpleo(models.Model):
    _name = 'sat.nomina.tabla_subsidio'
    _description = 'SAT - Tabla Subsidio al Empleo.'
    _order = "sequence, tipo, vigencia, limite_inferior"
    
    @api.depends('tipo')
    def _compute_seq(self):
        seq = {'diaria'     : 10,
               'semanal'    : 20,
               'decenal'    : 30,
               'quincenal'  : 40,
               'mensual'    : 50,
               'anual'      : 60,
              }
        for rec in self:
            rec.sequence = seq[rec.tipo]
    
    @api.depends('vigencia', 'limite_inferior', 'limite_superior')
    def _compute_name(self):
        for rec in self:
            if rec.vigencia and rec.limite_inferior and rec.limite_superior:
                val = dict(rec.fields_get(allfields=['tipo'])['tipo']['selection'])[rec.tipo]
                rec.name = 'Para Nómina: ' + val + ' - ' +  rec.vigencia.strftime('%Y-%m-%d') + _(' - Límite Inf: ') + str(rec.limite_inferior) + _(' - Límite Sup: ') + str(rec.limite_superior)
            else:
                rec.name = '/'
    
    name = fields.Char('Descripción', store=True, compute='_compute_name')
    limite_inferior = fields.Float('Límite Inferior', digits=(18,2), required=True, index=True)
    limite_superior = fields.Float('Límite Superior', digits=(18,2), required=True, index=True)
    subsidio        = fields.Float('Subsidio', digits=(18,2), required=True)
    vigencia        = fields.Date('Vigencia', required=True)
    tipo            = fields.Selection([('diaria', 'Diaria'),
                                        ('semanal', 'Semanal'),
                                        ('decenal', 'Decenal'),
                                        ('quincenal', 'Quincenal'),
                                        ('mensual', 'Mensual'),
                                        ('anual', 'Anual'),
                                       ], string="Aplica a Nómina", default='quincenal', required=True)
    sequence        = fields.Integer(string="Sec", compute='_compute_seq', store=True)
    
##### Tabla para Dias de Vacaciones
class HRPayroll_TablaVacaciones(models.Model):
    _name = 'sat.nomina.tabla_vacaciones'
    _description = 'SAT - Tabla para Dias de Vacaciones.'

    @api.depends('antiguedad')
    def _compute_name(self):
        for rec in self:
            if rec.antiguedad:
                rec.name = _('Antigüedad:') + str(rec.antiguedad)
            else:
                rec.name = '/'
    
    name = fields.Char('Descripción', store=True, compute='_compute_name')
    antiguedad  = fields.Integer('Antigüedad', required=True, index=True)
    dias        = fields.Integer('Días', required=True)
    
    
    

###### c_OrigenRecurso #########

class HRPayroll_c_OrigenRecurso(models.Model):
    _name = 'sat.nomina.origenrecurso'
    _description = 'SAT - Catálogo del tipo de origen recurso.'
    _order = 'code'

    code = fields.Char('Código', required=True)
    name = fields.Char('Descripción', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)','El Código debe ser único')]    

    
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
    
    
###### c_PeriodicidadPago #########    
class HRPayroll_c_PeriodicidadPago(models.Model):
    _name = "sat.nomina.periodicidadpago"
    _description = 'SAT - Catálogo de tipos de periodicidad del pago.'
    _order = 'code'
    
    code = fields.Char(string="Código", size=8, required=True, index=True)
    name = fields.Text(string="Descripción", required=True, index=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin")
    dias = fields.Float(string="Días", digits=(6,1), default=0.0)
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El Código debe ser único')]
    
    
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
    
    
###### c_TipoContrato #########
class HRPayroll_c_TipoContrato(models.Model):
    _name = 'sat.nomina.tipocontrato'
    _description = 'SAT - Catálogo de tipos de contrato.'
    _order = 'code'
    
    code = fields.Char('Código', required=True)
    name = fields.Char('Descripción', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)','El Código debe ser único')]    

    
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
    
    
###### c_TipoDeduccion #########    
class HRPayroll_c_TipoDeduccion(models.Model):
    _name = "sat.nomina.tipodeduccion"
    _description = 'SAT - Catálogo de tipos de deducciones.'
    _order = 'code'
    
    code = fields.Char(string="Código", size=8, required=True, index=True)
    name = fields.Text(string="Descripción", required=True, index=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin")
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El Código debe ser único')]
    
    
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
    
    
###### c_TipoHoras #########
class HRPayroll_c_TipoHoras(models.Model):
    _name = 'sat.nomina.tipohoraextra'
    _description = 'SAT - Catálogo de tipos de Horas Extra.'
    _order = 'code'
    
    code = fields.Char('Código', required=True)
    name = fields.Char('Descripción', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)','El Código debe ser único')]    

    
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

    
###### c_TipoIncapacidad #########
class HRPayroll_c_TipoIncapacidad(models.Model):
    _name = 'sat.nomina.tipoincapacidad'
    _description = 'SAT - Catálogo de tipos de Incapacidad.'
    _order = 'code'
    
    code = fields.Char('Código', required=True)
    name = fields.Char('Descripción', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)','El Código debe ser único')]    

    
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


###### c_TipoJornada #########
class HRPayroll_c_TipoJornada(models.Model):
    _name = 'sat.nomina.tipojornada'
    _description = 'SAT - Catálogo de tipos de Jornada Laboral.'
    _order = 'code'

    code = fields.Char('Código', required=True)
    name = fields.Char('Descripción', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)','El Código debe ser único')]    

    
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

    
###### c_TipoNomina #########
class HRPayroll_c_TipoNomina(models.Model):
    _name = 'sat.nomina.tiponomina'
    _description = 'SAT - Catálogo de tipos de Nómina.'
    _order = 'code'

    code = fields.Char('Código', required=True)
    name = fields.Char('Descripción', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)','El Código debe ser único')]    

    
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
    
    

###### c_TipoOtroPago #########
class HRPayroll_c_TipoOtroPago(models.Model):
    _name = 'sat.nomina.tipootropago'
    _description = 'SAT - Catálogo de Otros tipos de Pago.'
    _order = 'code'

    code = fields.Char('Código', required=True)
    name = fields.Char('Descripción', required=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin")

    _sql_constraints = [
        ('code_unique', 'unique(code)','El Código debe ser único')]    

    
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
    

###### c_TipoPercepcion #########    
class HRPayroll_c_TipoPercepcion(models.Model):
    _name = "sat.nomina.tipopercepcion"
    _description = 'SAT - Catálogo de tipos de percepciones.'
    _order = 'code'
    
    code = fields.Char(string="Código", size=8, required=True, index=True)
    name = fields.Text(string="Descripción", required=True, index=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin")
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El Código debe ser único')]
    
    
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
    

###### c_TipoRegimen #########    
class HRPayroll_c_TipoRegimen(models.Model):
    _name = "sat.nomina.tiporegimen"
    _description = 'Catálogo de tipos de régimen de contratación.'
    _order = 'code'
    
    code = fields.Char(string="Código", size=8, required=True, index=True)
    name = fields.Text(string="Descripción", required=True, index=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin")
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El Código debe ser único')]
    
    
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
    
    
###### c_RiesgoPuesto #########    
class HRPayroll_c_RiesgoPuesto(models.Model):
    _name = "sat.nomina.riesgopuesto"
    _description = 'Catálogo de clases en que deben inscribirse los patrones.'
    _order = 'code'
    
    code = fields.Char(string="Código", size=8, required=True, index=True)
    name = fields.Text(string="Descripción", required=True, index=True)
    vigencia_inicio = fields.Date(string="Vigencia Inicio", required=True)
    vigencia_fin    = fields.Date(string="Vigencia Fin")
    prima            = fields.Float('Prima de Riesgo de Trabajo (%)', digits=(18,6), required=True, default=0)
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El Código debe ser único')]
    
    
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
    


##### Tabla Prestaciones
class HRPayroll_Prestaciones(models.Model):
    _name = 'sat.nomina.prestaciones'
    _description = 'SAT - Prestaciones'

    name = fields.Char(string="Categoría", required=True, index=True)
    description = fields.Text(string="Descripción")
    active = fields.Boolean(string="Activo", readonly=True, default=True)
    company_id          = fields.Many2one('res.company', string='Compañía', 
        default=lambda self: self.env.company)

    prestacion_premio_puntualidad = fields.Float(string="Premio x Puntualidad", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el Premio por Puntualidad (Por ejemplo: 10.00 para referirse a 10%)",
        default=0)
    prestacion_premio_asistencia  = fields.Float(string="Premio x Asistencia", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el Premio por Asistencia (Por ejemplo: 10.00 para referirse a 10%)",
        default=0)
    prestacion_vales_despensa  = fields.Float(string="Vales de Despensa", digits=(10,4), required=True,
        help="Indique el monto diario para Vales de Despensa", default=0)
    prestacion_fondo_ahorro    = fields.Float(string="Fondo de Ahorro", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el concepto de Fondo de Ahorro (Por ejemplo: 5.00 para referirse a 5%)",
        default=0)
    prestacion_caja_ahorro    = fields.Float(string="Caja de Ahorro", digits=(8,2), required=True,
        help="Indique el porcentaje a usar para el concepto de Caja de Ahorro (Por ejemplo: 7.5 para referirse a 7.5%)",
        default=0)
    prestacion_subsidio_por_incapacidad = fields.Boolean(string="Aplicar Subsidio por Incapacidad", 
        help="Active si el trabajador tendrá la prestación de Subsidio por incapacidad, esto es, cuando el trabajador tenga incapacidad.")

    prima_dominical = fields.Float(string="% Prima Dominical", default=25, digits=(8,2))

    line_ids = fields.One2many('sat.nomina.prestaciones.line', 'category_id', string="Líneas")

    _sql_constraints = [
        ('company_name_uniq', 'unique(company_id, name)', 'Categoría debe ser únicos por Compañía !'),
        ('check_prima_dominical', 'CHECK(prima_dominical >=25)', 'El porcentaje para la Prima Dominical no puede ser menor a 25')
        ]
    
##### Tabla Prestaciones
class HRPayroll_PrestacionesLineas(models.Model):
    _name = 'sat.nomina.prestaciones.line'
    _description = 'SAT - Prestaciones - Lineas'
    _order = "category_id, sindicalizado, antiguedad"

    @api.depends('sindicalizado', 'antiguedad')
    def _compute_name(self):
        for rec in self:
            rec.name = _('Categoría: ') + (rec.category_id.name or '') + _('Tipo Prestación: ') + dict(rec._fields['sindicalizado'].selection).get(rec.sindicalizado) + _(' - Antigüedad:') + str(rec.antiguedad)
            
    
    @api.depends('dias_vacaciones','dias_aguinaldo','prima_vacacional')
    def _get_factor_integracion(self):
        for rec in self:
            sueldo = 1.0
            monto_sueldo_anual = sueldo * 365.0
            monto_vacaciones = sueldo * rec.dias_vacaciones
            monto_prima_vacacional = monto_vacaciones * (rec.prima_vacacional / 100.0)
            monto_aguinaldo = sueldo * rec.dias_aguinaldo
            rec.factor_integracion = (monto_sueldo_anual + monto_prima_vacacional + monto_aguinaldo) / 365.0

    name = fields.Char('Descripción', store=True, compute='_compute_name')
    category_id = fields.Many2one('sat.nomina.prestaciones', string="Categoría", required=True,
        ondelete="cascade")    
    sindicalizado = fields.Selection([('Si','Sindicalizado'),
                                      ('No','De Confianza'),],
                                     string="Tipo Trabajador", default='No',
                                    required=True)
    
    antiguedad  = fields.Integer('Antigüedad', required=True, index=True)
    
    dias_vacaciones = fields.Integer('Días Vacaciones', required=True, default=0)
    prima_vacacional = fields.Float(string="% Prima Vac.", default=25, digits=(8,2))
    
    dias_aguinaldo = fields.Integer('Días Aguinaldo', required=True, default=15)

    

    factor_integracion = fields.Float(string="Factor Integración", compute="_get_factor_integracion",
        digits=(12,8))
    company_id          = fields.Many2one(related="category_id.company_id", store=True)
    
    _sql_constraints = [
        ('company_categ_antig_sindical_uniq', 'unique(company_id, category_id, antiguedad, sindicalizado)', 'Categoría + Antigüedad + Tipo Trabajador (De confianza | Sindicalizado) deben ser únicos !'),
        ('check_dias_aguinaldo', 'CHECK(dias_aguinaldo >=15)', 'Los días para Aguinaldo no puede ser menor a 15.'),
        ('check_prima_vacacional', 'CHECK(prima_vacacional >=25)', 'El porcentaje para la Prima Vacacional no puede ser menor a 25'),
        ]

    
##### Tabla ISN
class HRPayroll_ISN(models.Model):
    _name = 'sat.nomina.isn'
    _description = 'SAT - Tabla Porcentajes ISN'
    _rec_name = 'state_id'

    state_id = fields.Many2one('res.country.state', string="Estado", required=True, index=True)
    description = fields.Text(string="Descripción")
    
    percent = fields.Float(string="Porcentaje", digits=(5,2), required=True)
    active = fields.Boolean(string="Activo", readonly=True, default=True)
    vigencia    = fields.Date(string="Vigente Desde")

    _sql_constraints = [
        ('state_vigencia_uniq', 'unique(state_id, vigencia)', 'El registro debe ser único para el Estado y Vigencia !'),
        ]
    
