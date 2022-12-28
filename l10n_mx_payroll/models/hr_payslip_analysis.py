# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools
import logging
_logger = logging.getLogger(__name__)

class hr_payslip_analysis(models.Model):
    _name = "hr.payslip.analysis"
    _description = "Payslip Analisys"
    _auto = False
    _order = "number, date_to, nomina_aplicacion asc, salary_rule_id, amount desc, employee_id, payslip_run_id"

    contract_sindicalizado = fields.Selection(
        [('Si','Sindicalizado'),
         ('No','No Sindicalizado')], string="Sindicalizado", readonly=True)
    contract_department_id = fields.Many2one('hr.department', string="Departamento", readonly=True)
    work_location = fields.Char(string="Lugar de Trabajo", readonly=True)

    
    number      = fields.Char(string='Nómina', readonly=True)
    name        = fields.Char(string='Descripción', readonly=True)
    date        = fields.Date(string='Fecha', readonly=True)
    date_payroll= fields.Date(string='Fecha Pago', readonly=True)
    date_from   = fields.Date(string='Fecha Inicial', readonly=True)
    date_to     = fields.Date(string='Fecha Final', readonly=True)
    employee_id   = fields.Many2one('hr.employee', string='Empleado', readonly=True)
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla Salarial', readonly=True)
    code        = fields.Char(string='Código', readonly=True)
    concepto        = fields.Char(string='Concepto', readonly=True)
    category_id = fields.Many2one('hr.salary.rule.category', string='Categoría', readonly=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato', readonly=True)
    currency_id   = fields.Many2one('res.currency', string='Currency', readonly=True)
    quantity    = fields.Float(string="Qty", digits=(18,4), readonly=True)
    state = fields.Selection([
                                ('draft', 'Draft'),
                                ('verify', 'Waiting'),
                                ('done', 'Done'),
                                ('cancel', 'Rejected'),
                            ], string='Estado', readonly=True)
    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
                                readonly=True)
    amount          = fields.Monetary(string='Monto', readonly=True)
    cfdi_fecha_timbrado = fields.Datetime(string='Fecha Timbrado', readonly=True)
    tiponomina_id   = fields.Many2one('sat.nomina.tiponomina','Tipo Nómina', readonly=True)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Lista de Nómina', readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)
    
    tipo_gravable           = fields.Selection([('gravable' , 'Gravable'),
                                                ('exento'   , 'Exento')],
                                               string="Tipo Gravamen", readonly=True)
    
    nomina_aplicacion       = fields.Selection([('percepcion','Percepción'),
                                                ('deduccion', 'Deducción'),
                                                ('otrospagos', 'Otros Pagos'),
                                                ('incapacidad', 'Incapacidad'),
                                                ('no_aplica', 'No Aplica')],
                                               string="Uso en Nómina", readonly=True)
    tipopercepcion_id   = fields.Many2one('sat.nomina.tipopercepcion', string="·Tipo Percepción", readonly=True)
    tipodeduccion_id    = fields.Many2one('sat.nomina.tipodeduccion', string="·Tipo Deducción", readonly=True)
    tipootropago_id     = fields.Many2one('sat.nomina.tipootropago', string="·Tipo Otro Pago", readonly=True)
    tipoincapacidad_id  = fields.Many2one('sat.nomina.tipoincapacidad', string="·Tipo Incapacidad", readonly=True)
    no_suma             = fields.Boolean(string="No suma", readonly=True)
    es_subsidio_causado = fields.Boolean(string="Es Subsidio Causado", readonly=True)
    settlement_id       = fields.Many2one('hr.settlement', string="Finiquito", readonly=True)
    job_id       = fields.Many2one('hr.job', string="Puesto", readonly=True)
    
    def query_select(self):
        return """
select l.id, 
nomina.company_id,
nomina.number, nomina.name, nomina.date, nomina.date_payroll, nomina.state, nomina.struct_id,
nomina.payslip_run_id, nomina.settlement_id, contract.job_id,
nomina.contract_department_id, employee.work_location, nomina.contract_sindicalizado,
nomina.date_from, nomina.date_to, employee.id employee_id, l.salary_rule_id, l.code, 
l.name concepto, l.category_id, l.contract_id, l.quantity, 
case when rule.nomina_aplicacion='deduccion' then l.amount * -1.0 else l.amount end amount,
nomina.cfdi_folio_fiscal, nomina.cfdi_fecha_timbrado, j.currency_id, dept.id department_id, nomina.tiponomina_id,
rule.tipo_gravable, rule.nomina_aplicacion,
rule.tipopercepcion_id, rule.tipodeduccion_id,
rule.tipootropago_id, rule.tipoincapacidad_id, rule.no_suma, rule.es_subsidio_causado
        """
    
    def query_from(self):
        return """
from hr_payslip nomina
    inner join hr_contract contract on contract.id=nomina.contract_id
	inner join hr_employee employee on nomina.employee_id=employee.id
	left join hr_department dept on dept.id=employee.department_id
	inner join hr_payslip_line l on l.slip_id=nomina.id
	inner join account_journal j on j.id=nomina.journal_id
    inner join hr_salary_rule rule on rule.id=l.salary_rule_id
        """
    
    def query_where(self):
        return """
        ;
        """
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        create index on hr_payslip_line (slip_id, employee_id, contract_id, company_id, salary_rule_id);
        CREATE or REPLACE VIEW %s as 
        %s
        %s
        %s
        """ % (self._table, self.query_select(), self.query_from(), self.query_where()))


class hr_payslip_analysis_extrahours(models.Model):
    _name = "hr.payslip.analysis_extrahours"
    _description = "Analisis de Horas Extras"
    _auto = False
    _order = "number, date_to, employee_id, payslip_run_id"

    contract_sindicalizado = fields.Selection(
        [('Si','Sindicalizado'),
         ('No','No Sindicalizado')], string="Sindicalizado", readonly=True)
    contract_department_id = fields.Many2one('hr.department', string="Departamento", readonly=True)
    work_location = fields.Char(string="Lugar de Trabajo", readonly=True)

    
    number      = fields.Char(string='Nómina', readonly=True)
    name        = fields.Char(string='Descripción', readonly=True)
    date        = fields.Date(string='Fecha', readonly=True)
    date_payroll= fields.Date(string='Fecha Pago', readonly=True)
    date_from   = fields.Date(string='Fecha Inicial', readonly=True)
    date_to     = fields.Date(string='Fecha Final', readonly=True)
    employee_id   = fields.Many2one('hr.employee', string='Empleado', readonly=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato', readonly=True)
    currency_id   = fields.Many2one('res.currency', string='Currency', readonly=True)
    state = fields.Selection([
                                ('draft', 'Draft'),
                                ('verify', 'Waiting'),
                                ('done', 'Done'),
                                ('cancel', 'Rejected'),
                            ], string='Estado', readonly=True)
    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
                                readonly=True)
    cfdi_fecha_timbrado = fields.Datetime(string='Fecha Timbrado', readonly=True)
    tiponomina_id   = fields.Many2one('sat.nomina.tiponomina','Tipo Nómina', readonly=True)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Lista de Nómina', readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)
    
    settlement_id       = fields.Many2one('hr.settlement', string="Finiquito", readonly=True)
    job_id       = fields.Many2one('hr.job', string="Puesto", readonly=True)
    
    extra_hours_gravado = fields.Monetary(string="H.E. Gravadas", readonly=True)
    extra_hours_exento  = fields.Monetary(string="H.E. Exentas", readonly=True)
    extra_hours_monto_simple = fields.Monetary(string="Monto H.E. Simples", readonly=True)
    extra_hours_monto_doble = fields.Monetary(string="Monto H.E. Dobles", readonly=True)
    extra_hours_monto_triple = fields.Monetary(string="Monto H.E. Triples", readonly=True)
    extra_hours_monto   = fields.Monetary(string="Monto H.E. Total", readonly=True)
    extra_hours_qty = fields.Integer(string="Cant H.E. Total", readonly=True)
    extra_hours_qty_simple = fields.Integer(string="Cant H.E. Simples", readonly=True)
    extra_hours_qty_doble = fields.Integer(string="Cant H.E. Dobles", readonly=True)
    extra_hours_qty_triple = fields.Integer(string="Cant H.E. Triple", readonly=True)
    extra_hours_dias = fields.Integer(string="Dias H.E. Total", readonly=True)
    extra_hours_dias_simple = fields.Integer(string="Dias H.E. Simples", readonly=True)
    extra_hours_dias_doble = fields.Integer(string="Dias H.E. Dobles", readonly=True)
    extra_hours_dias_triple = fields.Integer(string="Dias H.E. Triples", readonly=True)


    def query_select(self):
        return """
select nomina.id, nomina.company_id,
nomina.number, nomina.name, nomina.date, nomina.date_payroll, nomina.state, nomina.struct_id,
nomina.payslip_run_id, nomina.settlement_id, contract.job_id,
nomina.contract_department_id, employee.work_location, nomina.contract_sindicalizado,
nomina.date_from, nomina.date_to, employee.id employee_id, nomina.tiponomina_id,
nomina.extra_hours_gravado, nomina.extra_hours_exento, nomina.extra_hours_monto,
nomina.extra_hours_monto_simple, nomina.extra_hours_monto_doble, nomina.extra_hours_monto_triple,
nomina.extra_hours_qty_simple, nomina.extra_hours_qty_doble, nomina.extra_hours_qty_triple,
nomina.extra_hours_qty,
nomina.extra_hours_dias_simple, nomina.extra_hours_dias_doble, nomina.extra_hours_dias_triple,
nomina.extra_hours_dias
        """
    
    def query_from(self):
        return """
from hr_payslip nomina
    inner join hr_contract contract on contract.id=nomina.contract_id
    inner join hr_employee employee on nomina.employee_id=employee.id
        """
    
    def query_where(self):
        return """
        ;
        """
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        CREATE or REPLACE VIEW %s as 
        %s
        %s
        %s
        """ % (self._table, self.query_select(), self.query_from(), self.query_where()))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: