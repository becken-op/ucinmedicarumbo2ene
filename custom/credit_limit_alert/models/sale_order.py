from odoo import models, fields, api, exceptions,_
from datetime import datetime, date, time, timedelta
import calendar

# class SaleConfigSettings(models.Model):
#     _inherit = "res.company"
#     days_of_delay = fields.Integer(string="Dias de espera.", related="company_id.days_of_delay")
#     inmediate_payment = fields.Many2one('account.payment.term',string="Termino de pago inmediato")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    days_of_delay = fields.Integer(string="Dias de espera.", config_parameter='sale.days_of_delay', default=0)
    inmediate_payment = fields.Many2one('account.payment.term',string="Termino de pago inmediato",config_parameter='sale.inmediate_payment')

class CreditLimitAlertSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    permitted_credit_limit = fields.Boolean('Limite de credito excedido permitido', default=False)
    paid_sale_order = fields.Boolean('Pedido Pagado', default=False)

    def action_confirm(self):
        param = self.env['ir.config_parameter'].sudo()
        current_date = date.today() - timedelta(days=int(param.get_param('sale.days_of_delay')))
        cr = self.env.cr

        sql = ""

        if self.partner_id.parent_id:
            sql = "select COALESCE(SUM(1),0) FROM account_move WHERE move_type='out_invoice' AND payment_state in ('not_paid', 'partial') AND state='posted' AND invoice_date_due<='"+str(current_date)+"' AND (partner_id='"+str(self.partner_id.id)+"' OR partner_id='"+str(self.partner_id.parent_id.id)+"')"
        else:
            sql = "select COALESCE(SUM(1),0) FROM account_move WHERE move_type='out_invoice' AND payment_state in ('not_paid', 'partial') AND state='posted' AND invoice_date_due<='"+str(current_date)+"' AND partner_id='"+str(self.partner_id.id)+"'"

        cr.execute(sql)
        facturas_vencidas = cr.fetchone()
        fac = max(facturas_vencidas)
        
        pago_in = param.get_param('sale.inmediate_payment')
        
        # p = self.env['account.payment.term'].search([('id','=',pago_in)], limit=1)
        # print(p.name, " -------> ", n_days)
        #pago_in = self.company_id.inmediate_payment.id

        if self.partner_id.block_sales==True:
            raise exceptions.ValidationError('El cliente tiene bloqueadas las ventas')

        if self.partner_id.parent_id.block_sales==True:
            raise exceptions.ValidationError('La compañia del cliente tiene bloqueadas las ventas')

        if not self.payment_term_id:
            raise exceptions.ValidationError('Necesita seleccionar un plazo de pago.')

        if (self.payment_term_id.id==pago_in and self.paid_sale_order!=True):
            raise exceptions.ValidationError('Si el pago es inmediato necesita validar que esta orden esté pagada')

        if (fac >= 1 and self.payment_term_id.id != pago_in and self.permitted_credit_limit is not True):
            raise exceptions.ValidationError('Este cliente o la empresa a la que pertenece tiene facturas vencidas.')
        else:
            if self.partner_id.credit_limit != 0:
                credit = self.env['res.currency']._compute(self.company_id.currency_id,self.currency_id,self.partner_id.credit)
                credit_limit = self.env['res.currency']._compute(self.company_id.currency_id,self.currency_id,self.partner_id.credit_limit)
                c_credit = self.env['res.currency']._compute(self.company_id.currency_id,self.currency_id,self.partner_id.parent_id.credit)
                c_credit_limit = self.env['res.currency']._compute(self.company_id.currency_id,self.currency_id,self.partner_id.credit_limit)

                
                if credit + self.amount_total > credit_limit:
                    if self.payment_term_id.id != pago_in:
                        if self.permitted_credit_limit is not True:
                            # self.avisado = True
                            raise exceptions.ValidationError('Este cliente ha exedido el limite de credito. Su limite actual es: '
                                                             + str(self.partner_id.credit_limit) +', actualmente tiene una deuda de: '
                                                             + str(self.partner_id.credit) + ' y disponible tiene '
                                                             + str(self.partner_id.credit_available)
                                                             + ', debe de autorizar el limite de credito excedido' )

                if c_credit + self.amount_total > c_credit_limit:
                    if self.payment_term_id.id != pago_in:
                        if self.permitted_credit_limit is not True:
                            # self.avisado = True
                            raise exceptions.ValidationError('La compañia del cliente ha exedido el limite de credito. Su limite actual es: '
                                                             + str(self.partner_id.parent_id.credit_limit) +', actualmente tiene una deuda de: '
                                                             + str(self.partner_id.parent_id.credit) + ' y disponible tiene '
                                                             + str(self.partner_id.parent_id.credit_available)
                                                             + ', debe de autorizar el limite de credito excedido' )


            res = super(CreditLimitAlertSaleOrder, self).action_confirm()

            return res

class CreditLimitAlertStockPicking(models.Model):
    _name = "stock.picking"
    _inherit = 'stock.picking'

    allow_delivery = fields.Boolean('Permitir entrega con facturas vencidas', default=False)

    def button_validate(self):
        self.ensure_one()
        if self.partner_id:
            if self.picking_type_code == 'outgoing':
                current_date = date.today() - timedelta(days=15)
                cr = self.env.cr

                sql = ""

                if self.partner_id.parent_id:
                    sql = "select COALESCE(SUM(1),0) FROM account_move WHERE move_type='out_invoice' AND state='posted' AND payment_state in ('not_paid', 'partial') AND invoice_date_due<='"+str(current_date)+"' AND (partner_id='"+str(self.partner_id.id)+"' OR partner_id='"+str(self.partner_id.parent_id.id)+"')"
                else:
                    sql = "select COALESCE(SUM(1),0) FROM account_move WHERE move_type='out_invoice' AND state='posted' AND payment_state in ('not_paid', 'partial') AND invoice_date_due<='"+str(current_date)+"' AND partner_id='"+str(self.partner_id.id)+"'"

                cr.execute(sql)
                facturas_vencidas = cr.fetchone()
                fac = max(facturas_vencidas)
                if fac >= 1 and self.allow_delivery is not True:
                    raise exceptions.ValidationError('Este cliente o la empresa a la que pertenece tiene facturas vencidas.')
                else:
                    res = super(CreditLimitAlertStockPicking, self).button_validate()
                    return res
            else:
                res = super(CreditLimitAlertStockPicking, self).button_validate()
                return res

        else:
            res = super(CreditLimitAlertStockPicking, self).button_validate()
            return res