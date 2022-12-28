# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Lead(models.Model):
    _inherit = 'crm.lead'

    is_bid = fields.Boolean(
        string='Is Bid',
        tracking=True,
        default=False)
    bid_state = fields.Selection([
        ('quotation', 'Quotation'),
        ('awarded', 'Awarded'),
        ('void', 'Void'),
        ('cancel', 'Cancel'),
        ('market_research', 'Market research'),
        ], string='Status', copy=False, index=True, tracking=3, default='quotation')
    bid_type = fields.Selection([
        ('direct', 'Direct'),
        ('distributor', 'Distributor'),
        ], string='Bid Type', copy=False, tracking=1)
    bidder_id = fields.Many2one(
        'res.partner', string='Bidder',
        tracking=1)
    document_folio = fields.Char(string="Document Folio", tracking=True)
    bid_folio = fields.Char(string="Bid Folio", tracking=True)
    modality = fields.Selection([
        ('electronic', 'Electronic'),
        ('in_person', 'In Person'),
        ('mixed', 'Mixed'),
        ], string='Modality', copy=False, tracking=1)
    character = fields.Selection([
        ('national', 'National'),
        ('open_international', 'Open International'),
        ('under_treaties', 'Under Treaties'),
        ], string='Character', copy=False, tracking=1)
    return_samples = fields.Boolean(
        string='Return samples?',
        default=False)
    delivery_requirements = fields.Text(
        string='Requirements for Products Deliveries')
    bid_notes = fields.Text(
        string='Observations')
    # Fecha Junta Aclaraciones: Datetime
    clarifications_meeting_datetime = fields.Datetime(string="Clarifications Meeting", tracking=True)
    # FECHA DE ENTREGA DE MUESTRAS: Datetime
    sample_delivery_datetime = fields.Datetime(string="Sample Delivery", tracking=True)
    # FECHA DE ENTREGA DE PROPUESTAS TECNICA - ECONOMICA: Datetime
    proposals_delivery_date = fields.Date(
        string="Proposals Delivery Date", tracking=True,
        help='Date of delivery of technical-economic proposals',)
    # FECHA DE FALLO: Fecha
    decision_date = fields.Date(string="Decision Date", tracking=True)
    # VIGENCIA Inicio: Fecha
    effective_start_date = fields.Date(string="Effective Start Date", tracking=True)
    # VIGENCIA Fin: Fecha
    effective_end_date = fields.Date(string="Effective End Date", tracking=True)
    # EVENTO REALIZADO POR
    carried_out_id = fields.Many2one(
        'res.users', string='Carried out by',
        tracking=1)
    bid_deposit_ids = fields.Many2many(
        comodel_name='account.payment',
        column1='lead_id', column2='payment_id',
        string="Bonds or Checks",
        help='Define the bond or check as bid deposit.')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")
    # bid_line = fields.One2many('crm_lead.bid.line', 'bid_id', string='Bid Lines', copy=True, auto_join=True)


    def action_new_quotation(self):
        action = super(Lead, self).action_new_quotation()
        if self.pricelist_id:
            action['context'].update({'default_pricelist_id': self.pricelist_id.id})
            action['context']['default_is_bid'] = True
        return action

# class BidDeposit(models.Model):
#     _name = 'crm.bid.line'
#     _description = 'Bid deposit or check'