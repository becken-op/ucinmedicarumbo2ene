# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta, date
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)

class HREmployee(models.Model):
    _inherit = 'hr.employee'
    
    @api.depends('contract_ids', 'contract_ids.state', 'contract_ids.date_start', 'contract_ids.date_end')
    def _get_contrato_activo(self):
        ctx = self._context.copy()
        hoy = ctx.get('fecha') or datetime.now().date()
        for rec in self:            
            rec.con_contrato_activo = any([x.state=='open' and x.date_start <= hoy and \
                                             (x.date_end and x.date_end >= hoy or True) \
                                             for x in rec.contract_ids])
    
    def _search_get_contrato_activo(self, operator, value):
        ctx = self._context.copy()
        hoy = ctx.get('fecha') or datetime.now().date()

        contracts1 = self.env['hr.contract'].search([('date_start', '<=', hoy), ('date_end','=',False),
                                                     ('state','=','open')])
        contracts2 = self.env['hr.contract'].search([('date_start', '<=', hoy), ('date_end','!=',False),
                                                      ('date_end','>=',hoy), ('state','=','open')])
        contracts = contracts1 + contracts2
        
        if contracts:
            return [('id', 'in', [x.employee_id.id for x in contracts])]
        else:
            return [('id', 'in', [])]


    sdi_ids = fields.One2many('hr.contract.sdi','employee_id', 
                              string="Historial de SDIs", readonly=True)
    contract_sindicalizado = fields.Selection(related='contract_id.sindicalizado', store=True, index=True)
    contract_department_id = fields.Many2one('hr.department', string="Departamento (Contrato)",
                                             related="contract_id.department_id", store=True, index=True)
    struct_id = fields.Many2one('hr.payroll.structure', string="Estructura Salarial", 
                                related="contract_id.struct_id", store=True, readonly=True)
    con_contrato_activo = fields.Boolean(string="Tiene Contrato Activo", compute="_get_contrato_activo", 
                                         search="_search_get_contrato_activo", store=False)
    num_empleado= fields.Char(string="Número de Empleado", tracking=True)
    nss         = fields.Char(string="No. Seguro Social", tracking=True)
    curp        = fields.Char(string="CURP", tracking=True)
    
    infonavit_ids = fields.One2many('hr.employee.infonavit', 'employee_id', string="Infonavit", tracking=True)
    tipo_sangre = fields.Selection([('A+', 'A Positivo'),
                                    ('A-', 'A Negativo'),
                                    ('B+', 'B Positivo'),
                                    ('B-', 'B Negativo'),
                                    ('O+', 'O Positivo'),
                                    ('O-', 'O Negativo'),
                                    ('AB+', 'AB Positivo'),
                                    ('AB-', 'AB Negativo'),
                                    ], string="Tipo de Sangre", tracking=True)

    alergias    = fields.Char(string="Alergias")

    vat         = fields.Char(string="RFC", tracking=True)
    
    zip         = fields.Char(string="Código Postal", tracking=True)
    
    bank_id     = fields.Many2one('res.bank', string="Banco", tracking=True)
    
    bank_account_number = fields.Char(string="Cuenta Bancaria", tracking=True,
                             help="Indique el número de cuenta, tarjeta de débito o CLABE Interbancaria...")
    

    @api.depends('contract_id', 'contract_id.state')
    def _get_contract_data(self):        
        for rec in self:
            if rec.contract_id:
                #_logger.info("rec.contract_id.job_id: %s - %s" % (rec.contract_id.job_id.id, rec.contract_id.job_id.name))
                rec.job_id = rec.contract_id.job_id.id
                rec.department_id = rec.contract_id.department_id.id
            else:
                contract_obj = self.env['hr.contract']
                rec.job_id = None
                rec.department_id = None
                contracts = contract_obj.search([('employee_id','=',rec.id),
                                                 ('active','in',(True, False)),
                                                 ('state','not in',('draft','cancel'))], order='date_start desc')
                if contracts:
                    rec.job_id = contracts[0].job_id.id
                    rec.department_id = contracts[0].department_id.id

                
    job_id      = fields.Many2one('hr.job', compute="_get_contract_data", 
                                  store=True, index=True, tracking=True)
    department_id= fields.Many2one('hr.department', compute="_get_contract_data", 
                                   store=True, index=True, tracking=True)
    

    def name_get(self):
        result = []
        for rec in self:
            name = "[%s] %s" % (rec.num_empleado, rec.name)
            result.append((rec.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', '=ilike', '%' + name + '%'), ('num_empleado', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    
    @api.onchange('num_empleado')
    def _onchange_num_empleado(self):
        self.registration_number = self.num_empleado
    
    
    def _get_contracts(self, date_from, date_to, states=['open'], kanban_state=False):
        """
        Returns the contracts of the employee between date_from and date_to
        """
        state_domain = [('state', 'in', states)]
        if kanban_state:
            state_domain = expression.AND([state_domain, [('kanban_state', 'in', kanban_state)]])

        return self.env['hr.contract'].search(
            expression.AND([[('employee_id', 'in', self.ids)],
            state_domain,
            [('date_start', '<=', date_to),
                '|',
                    ('date_end', '=', False),
                    ('date_end', '>=', date_from)]]),
        order='employee_id, date_start desc')

class HREmployee_Infonavit(models.Model):
    _name = 'hr.employee.infonavit'
    _description = 'Infonavit por empleado'
    _order = "vigencia desc"

    name    = fields.Char('# Crédito', required=True)
    factor  = fields.Float('Factor/Monto', digits=(18,4), required=True)
    tipo    = fields.Selection([('veces_umi', 'Veces UMI'),
                                ('importe', 'Importe Fijo'),
                                ('porcentaje', 'Porcentaje (%)')],
                              string="Tipo de Cálculo", default='veces_umi', required=True)
    vigencia= fields.Date('Vigente desde', required=True)
    employee_id = fields.Many2one('hr.employee', string="Trabajador", required=True)
    
    _sql_constraints = [
        ('vigencia_unique', 'unique(employee_id, vigencia)','La vigencia debe ser única por trabajador')]
