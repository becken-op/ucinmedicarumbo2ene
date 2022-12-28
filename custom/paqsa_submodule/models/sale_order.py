#-*- coding: utf-8 -*-
from odoo import models, fields, api
class SaleOrder(models.Model):
    _inherit = 'sale.order.line'
        
    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)
            
            
            if pricelist_item.base == 'proveedor':
                field_name = 'proveedor'
                product_currency = product.cost_currency_id   
            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    name_account_id = fields.Char(
        'Factura nro',
        readonly=True,
        compute='_invoice_name')
    picking_percentage = fields.Float('Reservado',related='picking_ids.picking_percentage')
    delivery_percentage = fields.Float('Entregado',compute='_deliveri_p')
    invoiced_percentage = fields.Float('Facturado',compute='_deliveri_p')
    partner_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',string='Metodo de Pago') 
    partner_l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', 'Acquisition of merchandise'),
            ('G02', 'Returns, discounts or bonuses'),
            ('G03', 'General expenses'),
            ('I01', 'Constructions'),
            ('I02', 'Office furniture and equipment investment'),
            ('I03', 'Transportation equipment'),
            ('I04', 'Computer equipment and accessories'),
            ('I05', 'Dices, dies, molds, matrices and tooling'),
            ('I06', 'Telephone communications'),
            ('I07', 'Satellite communications'),
            ('I08', 'Other machinery and equipment'),
            ('D01', 'Medical, dental and hospital expenses.'),
            ('D02', 'Medical expenses for disability'),
            ('D03', 'Funeral expenses'),
            ('D04', 'Donations'),
            ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
            ('D06', 'Voluntary contributions to SAR'),
            ('D07', 'Medical insurance premiums'),
            ('D08', 'Mandatory School Transportation Expenses'),
            ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
            ('D10', 'Payments for educational services (Colegiatura)'),
            ('P01', 'To define'),
        ],
        string='Uso',
        default='P01',
        help='Used in CFDI 3.3 to express the key to the usage that will gives the receiver to this invoice. This '
             'value is defined by the customer.\nNote: It is not cause for cancellation if the key set is not the usage '
             'that will give the receiver of the document.')
    
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'l10n_mx_edi_usage' : self.partner_l10n_mx_edi_usage,
            'partner_payment_method_id': self.partner_payment_method_id.id,
            'l10n_mx_edi_payment_method_id': self.partner_payment_method_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_invoice_id.id)).id,
            'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals
    
    @api.onchange('invoice_ids')
    def _invoice_name(self): 
        for rec in self:
            invoice_name = str()
            for registro in rec.invoice_ids:
                invoice_name = registro.name
            rec.name_account_id = invoice_name
    
    @api.onchange('partner_id','partner_payment_method_id')
    def _payment_method(self): 
        for rec in self:
            default_payment_method_id = False
            for registro in rec.partner_id:
                default_payment_method_id = registro.l10n_mx_payment_method_id
            rec.partner_payment_method_id = default_payment_method_id
    
    @api.onchange('partner_id')
    def _l10n_mx_edi_usage(self): 
        for rec in self:
            mx_edi_usage_id = 'P01'
            for registro in rec.partner_id:
                mx_edi_usage_id = registro.l10n_mx_edi_usage
            rec.partner_l10n_mx_edi_usage = mx_edi_usage_id

    
    @api.depends('order_line', 'order_line.qty_delivered', 'order_line.qty_invoiced')
    def _deliveri_p(self): 
        for rec in self:
            qtyinvoiced = 0
            qtydelivered = 0
            productuom = 0
            for line in rec.order_line:
                qtydelivered += (line.qty_delivered)
                productuom += (line.product_uom_qty)
                qtyinvoiced += (line.qty_invoiced)
            rec.delivery_percentage = (qtydelivered / productuom )*100 
            rec.invoiced_percentage = (qtyinvoiced / productuom)*100
