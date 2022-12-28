# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, date, timedelta
from odoo.tools import float_compare, float_is_zero
from odoo.tools.safe_eval import safe_eval
import base64
import logging
_logger = logging.getLogger(__name__)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    tipo_movimiento = fields.Selection([('cargo','Cargo'),
                                        ('abono', 'Abono'),
                                        ('na', 'No se contabiliza')], default='na',
                                       string="Tipo Movimiento", required=True)
    
    account_line_ids = fields.One2many('hr.salary.rule.account_per_department', 'hr_salary_rule_id',
                                      string="Cuentas por Departamento")
    
    
    def get_account_per_department(self, company_id, department_id, slip):
        """
        Devuelve el ID de la cuenta contable relacionada al departamento
        """
        account_id, analytic_account_id = False, False
        #_logger.info("- - - - - - - - - - - - - - - - -")
        #_logger.info("Cuenta contable para: %s-%s" % (self.code, self.name))
        cuenta = self.env['hr.salary.rule.account_per_department'].search(
            [('hr_salary_rule_id','=',self.id),
             ('department_id','=',department_id.id),
             ('company_id','=',company_id)
            ], limit=1)
        if not cuenta:
            raise UserError(_("No se encontró la cuenta contable para:\nRegla Salarial: %s-%s\nDepartamento: [%s] %s\nEmpleado: [%s] %s") % (self.code, self.name, department_id.id, department_id.name, slip.employee_id.id, slip.employee_id.name))
        return cuenta.account_id, cuenta.analytic_account_id

    

    
class hr_payslip_analysis(models.Model):
    _inherit = "hr.payslip.analysis"
    
    tipo_movimiento = fields.Selection([('cargo','Cargo'),
                                        ('abono', 'Abono'),
                                        ('na', 'No se contabiliza')], 
                                       string="Tipo Movimiento Contable", readonly=True)
    

    def query_select(self):
        res = super(hr_payslip_analysis, self).query_select()
        return res + ", rule.tipo_movimiento"


class HrSalaryRuleAccountPerDepartment(models.Model):
    _name = 'hr.salary.rule.account_per_department'
    _description = "Cuentas por departamento"
    _rec_name = 'department_id'
    _order = 'department_id, account_id'
    
    
    account_id = fields.Many2one('account.account', 'Cuenta Contable', required=True,
                                 domain=[('deprecated', '=', False), ('internal_type','=','other')])
    
    analytic_account_id = fields.Many2one('account.analytic.account', 'Cuenta Analítica')
    department_id = fields.Many2one('hr.department', string='Departamento', required=True, index=True)
    company_id = fields.Many2one('res.company', string='Compañía', change_default=True,
                                 required=True, index=True,
                                 default=lambda self: self.env['res.company']._company_default_get('hr.salary.rule.account_per_department'))
    hr_salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla Salarial', required=True, index=True)
                                        
    tipo_movimiento = fields.Selection(related="hr_salary_rule_id.tipo_movimiento", readonly=False)
    
    _sql_constraints = [
        ('dept_acc_company_uniq', 'unique (company_id, hr_salary_rule_id, department_id, account_id, analytic_account_id)', 'El departamento + cuenta contable debe ser único por Compañía !')
    ]
    
    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    
    def crear_poliza(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        move_obj = self.env['account.move']
        for slip in self:
            if slip.state not in ('draft','verify','done') or slip.move_id:
                continue
            _logger.info("- - - - - - - - - - - - - -")
            _logger.info("Procesando Recibo: %s" % slip.name)
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            _logger.info("Creando Poliza...")
            name = '%s %s %s %s' % (_('Nómina: %s') % slip.number, 
                                    _('Empleado: %s') % slip.employee_id.name,
                                    slip.payslip_run_id and (_('Lista de Nóminas: %s') % slip.payslip_run_id.name) or '',
                                    slip.settlement_id and (_('Finiquito / Liquidación: %s') % slip.settlement_id.name) or '')
            
            ref = '%s %s %s' % (slip.number, 
                                slip.payslip_run_id and ('| ' + slip.payslip_run_id.name) or '',
                                slip.settlement_id and ('| ' + slip.settlement_id.name) or '')
                
            move_dict = {
                'narration': name,
                'ref': ref,
                'journal_id': slip.journal_id.id,
                'date': date,
                'payslip_id' : slip.id,
            }
            for line in slip.line_ids: #details_by_salary_rule_category:
                if not line.category_id:
                    continue
                if 'NET' in line.code:
                    amount = slip.neto_a_pagar
                else:
                    amount = slip.credit_note and -line.total or line.total
                if float_is_zero(amount, precision_digits=precision):
                    continue
                
                if line.salary_rule_id.tipo_movimiento!='na':
                    account_id, analytic_account_id = line.salary_rule_id.get_account_per_department(slip.company_id.id, slip.contract_id.department_id, slip)
                    account_move_line = (0, 0, {
                        'name'      : line.name,
                        'partner_id': slip.employee_id.address_home_id.id,
                        'account_id': account_id.id,
                        'journal_id': slip.journal_id.id,
                        'date'      : date,
                        'debit'     : line.salary_rule_id.tipo_movimiento=='cargo' and (amount > 0.0 and amount or 0.0) or 0.0,
                        'credit'    : line.salary_rule_id.tipo_movimiento=='abono' and (amount > 0.0 and amount or 0.0) or 0.0,
                        'analytic_account_id': analytic_account_id.id,
                        #'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(account_move_line)
                    if line.salary_rule_id.tipo_movimiento == 'cargo':
                        debit_sum += account_move_line[2]['debit'] - account_move_line[2]['credit']
                    else:
                        credit_sum += account_move_line[2]['credit'] - account_move_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Partida de Ajuste'),
                    'partner_id': slip.employee_id.address_home_id.id,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Partida de Ajuste'),
                    'partner_id': slip.employee_id.address_home_id.id,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = move_obj.create(move_dict)
            slip.write({'move_id': move.id, 'date': date, 'state' : 'done'})
            move.action_post()
            self.env.cr.commit()
            # Ponemos los descuentos de Fonacot "futuros" como Cancelados
            if slip.settlement_id:
                for line in slip.input_line_ids.filtered(lambda w: w.payslip_extra_id and \
                               w.payslip_extra_id.hr_salary_rule_id.id in slip.company_id.\
                               reglas_a_incluir_en_periodo_de_nomina_finiquito_ids.ids and \
                               w.payslip_extra_id.extra_discount_id):
                    extras = line.payslip_extra_id.extra_discount_id.payslip_extra_ids.filtered(lambda w: w.state in ('draft','confirmed','approved') and w.date > slip.date_to)
                    extras.action_cancel()
                # FIN: Ponemos los descuentos de Fonacot "futuros" como Cancelados
                self.env.cr.commit()
        return True
    
    
    def action_payslip_done(self):
        
        if any(slip.state == 'cancel' for slip in self):
            raise ValidationError(_("No puede Validar una Nómina Cancelada."))
        if any(not slip.line_ids for slip in self):
            self.filtered(lambda w: not w.line_ids).compute_sheet()
        self.crear_poliza()
        self.env.cr.commit()

        # Ponemos los descuentos de Fonacot "futuros" como Cancelados
        for slip in self.filtered(lambda w: w.settlement_id):
            # Ponemos los descuentos de Fonacot "futuros" como Cancelados
            for line in slip.input_line_ids.filtered(lambda w: w.payslip_extra_id and \
                           w.payslip_extra_id.hr_salary_rule_id.id in slip.company_id.\
                           reglas_a_incluir_en_periodo_de_nomina_finiquito_ids.ids and \
                           w.payslip_extra_id.extra_discount_id):
                extras = line.payslip_extra_id.extra_discount_id.payslip_extra_ids.filtered(lambda w: w.state in ('draft','confirmed','approved') and w.date > slip.date_to)
                extras.action_cancel()
            # FIN: Ponemos los descuentos de Fonacot "futuros" como Cancelados
        return True

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
