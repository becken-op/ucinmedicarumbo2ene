# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'mail.thread', 'mail.activity.mixin']

    bid_id = fields.Many2one(
        'crm.lead', string='Opportunity', check_company=True,
        related = 'order_id.opportunity_id',
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    is_bid = fields.Boolean(
        string='Is Bid',
        related='bid_id.is_bid',
        store=True,
        default=False)
    # BID LINE FIELDS
    bid_requisition = fields.Char(
        string='Requisition', size=10)
    basic_chart = fields.Char(
        string='Basic Chart')
    # Partida Presupuestal
    budget_line = fields.Char(
        string='Budget Line',
        tracking=True,)
    qty_min_requested = fields.Float(
        string='Qty Min Requested', digits='Product Unit of Measure', required=True, default=1.0)
    qty_max_requested = fields.Float(
        string='Qty Max Requested', digits='Product Unit of Measure', required=True, default=1.0)
    product_brand_ept_id = fields.Many2one(
        'product.brand.ept',
        related='product_id.product_tmpl_id.product_brand_ept_id',
        string='Brand',
        help='Select a brand for this product',)
    product_health_register_id = fields.Many2one(
        'product.health.register',
        related='product_id.product_tmpl_id.product_health_register_id',
        string="Health Register")
    manufactured_place = fields.Char(string="Fabricado en", related='product_id.product_tmpl_id.product_health_register_id.manufactured_place')
    reference_price = fields.Monetary('Reference Price', required=True, digits='Product Price', default=0.0)
    reference_supplier = fields.Char(string="Reference Supplier", tracking=True)
    last_purchase_price = fields.Float(
        compute="_compute_last_purchase_line_id_info",
        store=True,
        string="Last Purchase Price")
    last_purchase_date = fields.Datetime(
        compute="_compute_last_purchase_line_id_info",
        store=True,
        string="Last Purchase Date")
    last_purchase_supplier_id = fields.Many2one(
        comodel_name="res.partner",
        store=True,
        compute="_compute_last_purchase_line_id_info",
        string="Last Supplier",)
    last_purchase_currency_id = fields.Many2one(
        comodel_name="res.currency",
        store=True,
        compute="_compute_last_purchase_line_id_info",
        string="Last Purchase Currency",)

    # Total Mínimo "Calculado"
    # Total Máximo "Calculado"
    note = fields.Text('Observations')

    # Solo si se perdió:
    # Nombre del Participante
    awarded_supplier = fields.Char(string="Awarded Supplier", tracking=True)
    # Costo Participante
    awarded_supplier_price_unit = fields.Float(
        string='Awarded Unit Price',
        tracking=True,
        required=True, digits='Product Price', default=0.0)
    # Marca Participante
    awarded_product_brand = fields.Char(string="Awarded Brand", tracking=True, help='Select a brand for this product')
    # Procedencia Participante
    awarded_supplier_origin = fields.Char(
        string='Origin')

    # authorization_required = fields.Boolean(
    #     string="Authorization Required",
    #     tracking=True,)
    # authorization_date = fields.Datetime(
    #     string='Authorization date',
    #     tracking=True,)
    # authorization_comment = fields.Text(
    #     string='Authorization comment',
    #     tracking=True,)
    # authorization_user = fields.Many2one(
    #     'res.users', string='Authorization by', tracking=True)
    # authorized_user = fields.Boolean(
    #     compute="_compute_authorized_user",
    #     string="Authorized User")

    bid_line_state = fields.Selection([
        ('quotation', 'Quotation'),
        ('awarded', 'Awarded'),
        ('void', 'Void'),
        ('lost', 'Lost'),
        ], string='Status', copy=False, index=True, tracking=True, default='quotation')

    # RELATED FIELDS
    bid_partner_id = fields.Many2one(related='bid_id.partner_id', store=True, string='Customer', readonly=False)
    bid_type = fields.Selection(
        string='Bid Type', related='bid_id.bid_type', store=True, copy=False)
    bidder_id = fields.Many2one(
        'res.partner', string='Bidder',
        related='bid_id.bidder_id', store=True,)
    document_folio = fields.Char(string="Document Folio", related='bid_id.document_folio', store=True)
    bid_folio = fields.Char(string="Bid Folio", related='bid_id.bid_folio', store=True)
    modality = fields.Selection(
        string='Modality', related='bid_id.modality', store=True, copy=False)
    character = fields.Selection(
        string='Character', related='bid_id.character', store=True, copy=False)
    # TODO: Tal vez agregarlos como RELATED Y STORE=True
    # return_samples = fields.Boolean(
    #     string='Return samples?',
    #     default=False)
    # delivery_requirements = fields.Text(
    #     string='Requirements for Products Deliveries')
    # # Fecha Junta Aclaraciones: Datetime
    # clarifications_meeting_datetime = fields.Datetime(string="Clarifications Meeting")
    # # FECHA DE ENTREGA DE MUESTRAS: Datetime
    # sample_delivery_datetime = fields.Datetime(string="Sample Delivery")
    # # FECHA DE ENTREGA DE PROPUESTAS TECNICA - ECONOMICA: Datetime
    # proposals_delivery_date = fields.Date(
    #     string="Proposals Delivery Date",
    #     help='Date of delivery of technical-economic proposals',)
    # # FECHA DE FALLO: Fecha
    # decision_date = fields.Date(string="Decision Date")
    # # VIGENCIA Inicio: Fecha
    # effective_start_date = fields.Date(string="Effective Start Date")
    # # VIGENCIA Fin: Fecha
    # effective_end_date = fields.Date(string="Effective End Date")
    # # EVENTO REALIZADO POR
    # carried_out_id = fields.Many2one(
    #     'res.users', string='Carried out by',
    #     required=True)
    # bid_deposit_ids = fields.Many2many(
    #     comodel_name='account.payment',
    #     column1='lead_id', column2='payment_id',
    #     string="Bonds or Checks",
    #     help='Define the bond or check as bid deposit.')

    # def _compute_authorized_user(self):
    #     user_id = self.env.user
    #     for line in self:
    #         if line.authorization_user.id == line.env.uid or user_id.has_group('bck_crm_bid_management.bid_line_authorization_manager_group'):
    #             line.authorized_user = True
    #         else:
    #             line.authorized_user = False

    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        print('self.product_id.basic_chart: ', self.product_id.basic_chart)
        if self.product_id.basic_chart:
            self.basic_chart = self.product_id.basic_chart
            print('self.basic_chart: ', self.basic_chart)
        return result


    @api.depends("product_id", "bid_line_state")
    def _compute_last_purchase_line_id_info(self):
        for line in self:
            if line.is_bid:
                query = """
                    SELECT line.price_unit, po.date_approve, po.partner_id, po.currency_id
                    FROM purchase_order po
                    JOIN purchase_order_line line ON (po.id = line.order_id)
                    WHERE po.state in ('purchase', 'done') AND po.company_id = %s AND line.product_id = %s
                    ORDER BY date_approve DESC LIMIT 1;
                """
                self._cr.execute(query, (self.env.company.id, line.product_id.id))
                res = self.env.cr.fetchone()
                if res:
                    line.last_purchase_price = res[0]
                    line.last_purchase_date = res[1]
                    line.last_purchase_supplier_id = res[2]
                    line.last_purchase_currency_id = res[3]
                else:
                    line.last_purchase_price = False
                    line.last_purchase_date = False
                    line.last_purchase_supplier_id = False
                    line.last_purchase_currency_id = False
                
                # Actualizar automáticamente los campos: reference_price y reference_supplier
                query = """
                    SELECT line.price_unit, so.date_order, so.partner_id, so.currency_id
                    FROM sale_order so
                    JOIN sale_order_line line ON (so.id = line.order_id)
                    WHERE so.state in ('sale', 'done') AND so.company_id = %s AND line.product_id = %s
                    ORDER BY date_order DESC LIMIT 1;
                """
                self._cr.execute(query, (self.env.company.id, line.product_id.id))
                res = self.env.cr.fetchone()
                if res:
                    line.reference_price = res[0]
                    line.reference_supplier = res[2]
                else:
                    line.reference_price = False
                    line.reference_supplier = False


    def show_bid_line_form(self):
        view_id = self.env.ref('bck_crm_bid_management.crm_bid_sale_order_line_form_view').id
        context = self._context.copy()
        return {
            'name': 'Bid Line',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'form')],
            'res_model': 'sale.order.line',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'context': context,
        }

    # def write(self, vals):
    #     res = super(SaleOrderLine, self).write(vals)
    #     if 'authorization_user' in vals:
    #         activity_type_id = self.env.ref(
    #             "mail.mail_activity_data_todo").id
    #         model_id = self.env.ref("sale.model_sale_order_line").id
    #         for line in self:
    #             line.env["mail.activity"].sudo().create(
    #                 {
    #                     "activity_type_id": activity_type_id,
    #                     "summary": _("Bid Line Authorization: %s") % line.name,
    #                     "user_id": line.authorization_user.id,
    #                     "res_id": line.id,
    #                     "res_model_id": model_id,
    #                 }
    #             )
    #     return res

