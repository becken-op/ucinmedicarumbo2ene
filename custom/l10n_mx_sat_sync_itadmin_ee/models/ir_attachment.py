# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
from lxml import etree

import logging
_logger = logging.getLogger(__name__)

from .special_dict import CaselessDictionary
from odoo.exceptions import Warning


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    @api.depends('invoice_ids')
    def _compute_account_invoice_count(self):
        for attach in self:
            try:
                attach.invoice_count = len(attach.invoice_ids)
            except Exception:
                pass
            
    @api.depends('payment_ids')
    def _compute_account_payment_count(self):
        for attach in self:
            try:
                attach.payment_count = len(attach.payment_ids)
            except Exception:
                pass
                
    cfdi_uuid = fields.Char("CFDI UUID", copy=False)
    #cfdi_type = fields.Selection([('E','Emisor'),('R','Receptor')],"CFDI Invoice Type", copy=False)
    cfdi_type = fields.Selection([
        ('I', 'Facturas de clientes'), #customer invoice, Emisor.RFC=myself.VAT, Customer invoice
        ('SI', 'Facturas de proveedor'), #Emisor.RFC!=myself.VAT, Supplier bill
        ('E', 'Notas de crédito clientes'), #customer credit note, Emisor.RFC=myself.VAT, Customer credit note
        ('SE', 'Notas de crédito proveedor'), #Emisor.RFC!=myself.VAT, Supplier credit note
        ('P', 'REP de clientes'), #Emisor.RFC=myself.VAT, Customer payment receipt
        ('SP', 'REP de proveedores'), #Emisor.RFC!=myself.VAT, Supplier payment receipt
        ('N', 'Nominas de empleados'), #currently we shall not do anythong with this type of cfdi, Customer Payslip
        ('SN', 'Nómina propia'), #currently we shall not do anythong with this type of cfdi, Supplier Payslip
        ('T', 'Factura de traslado cliente'), #currently we shall not do anythong with this type of cfdi, WayBill Customer
        ('ST', 'Factura de traslado proveedor'),], #currently we shall not do anythong with this type of cfdi, WayBill Supplier                
        "Tipo de comprobante", 
        copy=False)

    date_cfdi = fields.Date('Fecha')
    rfc_tercero = fields.Char("RFC tercero")
    nombre_tercero = fields.Char("Nombre tercero")
    cfdi_total = fields.Float("Importe")
    creado_en_odoo = fields.Boolean("Creado en odoo", copy=False)
    invoice_ids = fields.One2many("account.move", 'attachment_id', "Facturas")
    invoice_count = fields.Integer(compute='_compute_account_invoice_count', string='# de facturas', store=True)
    
    payment_ids = fields.One2many("account.payment", 'attachment_id', "Pagos")
    payment_count = fields.Integer(compute='_compute_account_payment_count', string='# de pagos', store=True)
    
    serie_folio = fields.Char("Folio")
    
    # JCT
    l10n_mx_edi_sat_status = fields.Selection(
        selection=[
            ('none', "State not defined"),
            ('undefined', "Not Synced Yet"),
            ('not_found', "Not Found"),
            ('cancelled', "Cancelled"),
            ('valid', "Valid"),
        ],
        string="SAT status", readonly=True, copy=False, required=True, tracking=True,
        default='undefined',
        help="Refers to the status of the journal entry inside the SAT system.")
    l10n_mx_edi_sat_status_date = fields.Datetime(
        string="Status Updated On",
        copy=False,
        help="SAT status last update")
    
    # JCT
    # prodigia_supplier_invoice_validation agrega el campo supplier_uuid
    def action_automatic_reconcile(self):        
        invoice_type = {
            'I': 'out_invoice',
            'E': 'out_refund',
            'T': 'out_invoice',
            'SI': 'in_invoice',
            'SE': 'in_refund',
            'ST': 'in_invoice',
        }
        payment_type = {
            'P': 'outbound',
            'SP': 'inbound',
        }

        # Verificar sl account_move tiene el campo supplier_uuid
        if 'supplier_uuid' in self.env['account.move']._fields:
            supplier_uuid_exists = True
        else:
            supplier_uuid_exists = False
        
        for attachment_id in self:
            if not attachment_id.creado_en_odoo:
                # Facturas de Clientes o Proveedores
                if attachment_id.cfdi_type in invoice_type:
                    model = 'account.move'
                    if attachment_id.cfdi_type in ['SI', 'SE', 'ST'] and supplier_uuid_exists:
                        # Buscar por UUID (supplier_uuid del módulo prodigia_supplier_invoice_validation)
                        domain = [
                            ('supplier_uuid', 'ilike', attachment_id.cfdi_uuid),
                            ('move_type', '=', invoice_type[attachment_id.cfdi_type]),
                            ('state', '=', 'posted'),
                        ]
                    else:
                        # TODO: Verificar si buscar por UUID
                        if attachment_id.cfdi_type not in ['SI', 'SE', 'ST']:
                            domain = [
                                ('l10n_mx_edi_cfdi_uuid', 'ilike', attachment_id.cfdi_uuid),
                                ('move_type', '=', invoice_type[attachment_id.cfdi_type]),
                                ('state', '=', 'posted'),
                            ]
                        else:
                            # Buscar por:
                            #   Fecha de la factura: invoice_date
                            #   Proveedor: partner_id
                            #   Referencia de factura: ref
                            #   Total: amount_total_signed or amount_total
                            domain = [
                                ('partner_id.name', '=', attachment_id.nombre_tercero),
                                ('ref', '=', attachment_id.serie_folio),
                                ('amount_total', '=', attachment_id.cfdi_total),
                                ('move_type', '=', invoice_type[attachment_id.cfdi_type]),
                                ('state', '=', 'posted'),
                                '|',
                                ('invoice_date', '=', attachment_id.date_cfdi),
                                ('date', '=', attachment_id.date_cfdi),
                            ]
                # Pagos
                elif attachment_id.cfdi_type in ['P', 'SP']:
                    model = 'account.payment'
                    domain = [
                        ('partner_id.name', '=', attachment_id.nombre_tercero),
                        ('date', '=', attachment_id.date_cfdi),
                        ('payment_type', '=', payment_type[attachment_id.cfdi_type]),
                        ('amount', '=', attachment_id.cfdi_total),
                    ]
                _logger.info(f'Automatic reconciliation: Searching document {model} with domain {str(domain)}.')
                document_to_link_id = self.env[model].search(domain, limit=1)
                # Segunda búsqueda solo para facturas
                if not document_to_link_id and attachment_id.cfdi_type in invoice_type:
                    domain2 = [
                        ('partner_id.name', '=', attachment_id.nombre_tercero),
                        ('ref', '=', attachment_id.serie_folio),
                        ('amount_total', '=', attachment_id.cfdi_total),
                        ('move_type', '=', invoice_type[attachment_id.cfdi_type]),
                        ('state', '=', 'posted'),
                        '|',
                        ('invoice_date', '=', attachment_id.date_cfdi),
                        ('date', '=', attachment_id.date_cfdi),
                    ]
                    # No volver  abuscar si ya se buscó con el mismo dominio
                    if domain != domain2:
                        _logger.info(f'Automatic reconciliation: Searching document {model} with domain {str(domain)}.')
                        document_to_link_id = self.env[model].search(domain2, limit=1)
                if document_to_link_id:
                    _logger.info(f'Automatic reconciliation: Document found, Type: {attachment_id.cfdi_type}, UUID: {attachment_id.cfdi_uuid} reconcilied to document: {document_to_link_id.name}')
                    attachment_id.invoice_ids =  [(6, 0, document_to_link_id.ids)]
                    attachment_id.creado_en_odoo = True
                    # TODO: Verificar si ya existe el xml adjunto y eliminarlo, esto no aplica para facturas de clientes
                    if attachment_id.cfdi_type in ['SI', 'SE', 'ST']:
                        domain = [
                            ('res_id', '=', document_to_link_id.id),
                            ('res_model', '=', model),
                            ('name', 'ilike', attachment_id.cfdi_uuid+'.xml'),
                        ]
                        attachment_id = self.env['ir.attachment'].search(domain, limit=1)
                    attachment_id.res_model = model
                    attachment_id.res_id = document_to_link_id.id
                    document_to_link_id.attachment_id = attachment_id
                    

    # JCT
    def action_update_sat_status(self):
        if len(self) > 80:
            raise Warning(_('Please, select maximum 80 records tu update status, you have selected %s.') % len(self))

        for attachment in self:
            attachment.l10n_mx_edi_update_sat_status()


    def l10n_mx_edi_update_sat_status(self):
        '''Synchronize both systems: Odoo & SAT to make sure the invoice is valid.
        '''
        for attachment in self:
            if attachment.l10n_mx_edi_sat_status == 'cancelled':
                continue

            # Si es factura o nota de crédito de cliente
            if attachment.cfdi_type in ('I', 'E', 'P'):
                supplier_rfc = attachment.env.user.company_id.vat
                customer_rfc = attachment.rfc_tercero
            # Si es factura o nota de crédito de proveedor
            elif attachment.cfdi_type in ('SI', 'SE', 'SP'):
                supplier_rfc = attachment.rfc_tercero
                customer_rfc = attachment.env.user.company_id.vat
            else:
                continue
            total = attachment.cfdi_total
            uuid = attachment.cfdi_uuid

            try:
                status = self.env['account.edi.format']._l10n_mx_edi_get_sat_status(supplier_rfc, customer_rfc, total, uuid)
            except Exception as e:
                # Notificar error en el Log
                _logger.error('Error : '+_("Failure during update of the SAT status: %(msg)s", msg=str(e)))
                # attachment.message_post(body=_("Failure during update of the SAT status: %(msg)s", msg=str(e)))
                continue

            if status == 'Vigente':
                attachment.l10n_mx_edi_sat_status = 'valid'
            elif status == 'Cancelado':
                attachment.l10n_mx_edi_sat_status = 'cancelled'
            elif status == 'No Encontrado':
                attachment.l10n_mx_edi_sat_status = 'not_found'
            else:
                attachment.l10n_mx_edi_sat_status = 'none'
            attachment.l10n_mx_edi_sat_status_date = fields.Datetime.now()
            _logger.info(f'SAT Status Updated UUID: {uuid}, State: {status}')


    @api.model
    def create(self, vals):
        ctx = self._context.copy()
        if ctx.get('is_fiel_attachment'):
            datas = vals.get('datas')
            if datas:
                xml_content = base64.b64decode(datas)
                if b'xmlns:schemaLocation' in xml_content:
                    xml_content = xml_content.replace(b'xmlns:schemaLocation', b'xsi:schemaLocation')
                try:
                    tree = etree.fromstring(xml_content)
                except Exception as e:
                    _logger.error('error : '+str(e))
                    raise
                try:
                    ns = tree.nsmap
                    ns.update({'re': 'http://exslt.org/regular-expressions'})
                except Exception:
                    ns = {'re': 'http://exslt.org/regular-expressions'}
                    
                tfd_namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
                tfd_elements = tree.xpath("//tfd:TimbreFiscalDigital", namespaces=tfd_namespace)
                tfd_uuid = tfd_elements and tfd_elements[0].get('UUID')
                cfdi_type = vals.get('cfdi_type','I')
                
                if cfdi_type in ['I','E','P','N','T']:
                    element_tag = 'Receptor'
                else:
                    element_tag = 'Emisor'
                try:
                    elements = tree.xpath("//*[re:test(local-name(), '%s','i')]"%(element_tag), namespaces=ns)
                except Exception:
                    _logger.info("No encontró al Emisor/Receptor")
                    elements = None
                client_rfc, client_name = '', ''
                if elements:
                    attrib_dict = CaselessDictionary(dict(elements[0].attrib))
                    client_rfc = attrib_dict.get('rfc') 
                    client_name = attrib_dict.get('nombre')
                    
                vals.update({
                        'cfdi_uuid' :tfd_uuid,
                        'rfc_tercero' : client_rfc,
                        'nombre_tercero' : client_name,
                        'cfdi_total' : tree.get('Total', tree.get('total')),
                        'date_cfdi' : tree.get('Fecha',tree.get('fecha')),
                        'serie_folio' : tree.get('Folio',tree.get('folio'))
                    })
        return super(IrAttachment, self).create(vals)
    
    def action_view_payments(self):
        payments = self.mapped('payment_ids')
        if payments and payments[0].payment_type=='outbound':
            action = self.env.ref('account.action_account_payments_payable').sudo().read()[0]
        else:
            action = self.env.ref('account.action_account_payments').sudo().read()[0]
        
        if len(payments) > 1:
            action['domain'] = [('id', 'in', payments.ids)]
        elif len(payments) == 1:
            action['views'] = [(self.env.ref('account.view_account_payment_form').sudo().id, 'form')]
            action['res_id'] = payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
            
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
            action['view_mode'] = 'tree'
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').sudo().id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    def action_renmove_invoice_link(self):
        for attach in self:
            if attach.invoice_ids:
                attach.invoice_ids.write({'attachment_id' : False})
            if attach.payment_ids:
                attach.payment_ids.write({'attachment_id' : False})
            vals = {'res_id':False, 'res_model':False} #'l10n_mx_edi_cfdi_name':False
            if attach.creado_en_odoo:
                vals.update({'creado_en_odoo':False})
                #attach.creado_en_odoo=False
            attach.write(vals)
        return True

    def _read_group_allowed_fields(self):
        return super(IrAttachment,self)._read_group_allowed_fields() + ['creado_en_odoo', 'date_cfdi', 'nombre_tercero', 'serie_folio', 'create_date', 'rfc_tercero', 'cfdi_uuid', 'cfdi_type', 'cfdi_total']

