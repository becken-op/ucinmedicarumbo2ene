# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

import xmltodict
from lxml.objectify import fromstring
import base64
import zipfile
import io


class AccountMove(models.Model):
    _inherit = 'account.move'


    no_validate_xml = fields.Boolean(string="No validar XML",copy=False)
    supplier_uuid = fields.Char(string="UUID almacenado",
        copy=False,
        compute='_compute_supplier_uuid',
        store=True,
        help="""campo tecnico que almacena el uuid del xml adjunto
en facturas de proveedor""",
    )


    @api.depends('attachment_ids')
    def _compute_supplier_uuid(self):
        """
        obtener UUID de ultimo adjunto xml
        solo para facturas de proveedor
        """
        for rec in self:
            if rec.move_type == 'in_invoice':
                rec.supplier_uuid = rec.with_context({'compute': True}).get_xml_uuid() 


    def _post(self, soft=True):
        """
        HERENCIA A METODO DE VALIDACION DE FACTURA
        SE INCERTA FUNCIONALIDAD PARA VALIDAR XMLS
        """
        self.check_supplier_xml()
        return super(AccountMove,self)._post(soft)


    @api.model
    def retrieve_supplier_xml_attachments(self):
        """
        OBTIENE ADJUNTO XML DE LA FACTURA
        DEVUELVE EL PRIMER ADJUNTO .XML QUE ENCUENTRE
        """
        domain = [
            ('res_id', '=' , self.id),
            ('res_model', '=' ,self._name),
        ]
        xmls = self.env['ir.attachment'].search(domain)
        xmls = [xml for xml in xmls if xml.name.endswith('.xml') or xml.name.endswith('.XML')]
        return xmls and xmls[0] or False


    def validate_supplier_xml(self):
        """
        LEE ADJUNTO, REVISA SI ES XML
        Y LO VALIDA
        """
        self.ensure_one()
        attachment_id = self.retrieve_supplier_xml_attachments()
        if not attachment_id:
            raise ValidationError('No se encontro ningun archivo XML adjunto a esta factura!')

        xml = base64.decodebytes(attachment_id.datas)
        xml = xmltodict.parse(xml)
        allowed_margin = self.company_id.supplier_xml_amount_margin or 0.0

        root = xml['cfdi:Comprobante']
        receptor = root['cfdi:Receptor']
        emisor = root['cfdi:Emisor']

        rfc_emisor = emisor['@Rfc']
        rfc_receptor = receptor['@Rfc']

        xml_amount_untaxed = root['@SubTotal']
        xml_amount_total = root['@Total']

        #DATOS DE FACTUR
        invoice_partner = self.partner_id and self.partner_id.name or False
        invoice_partner_rfc = self.partner_id and self.partner_id.vat or False

        invoice_company = self.company_id and self.company_id.name or False
        invoice_company_rfc = self.company_id and self.company_id.vat or False

        invoice_amount_untaxed = self.amount_untaxed or 0.0
        invoice_amount_total = self.amount_total or 0.0


        if rfc_emisor != invoice_partner_rfc:
            raise ValidationError("""El RFC del emisor registrado en el XML no coincide 
con el registrado en Odoo!
RFC en xml: {}
RFC en Odoo: {}""".format(rfc_emisor,invoice_partner_rfc)
             )

        if rfc_receptor != invoice_company_rfc:
            raise ValidationError("""El RFC del receptor registrado en el XML no coincide 
con el registrado en Odoo!
RFC en xml: {}
RFC en Odoo: {}""".format(rfc_receptor,invoice_company_rfc)
             )

        difference = abs(round((float(xml_amount_total) - invoice_amount_total),2))
        if difference > allowed_margin:
            raise ValidationError("""El monto total registrado en el XML no coincide 
con el monto registrado en Odoo!
Monto en xml: {}
Monto en Odoo: {}""".format(str(xml_amount_total),str(invoice_amount_total))
             )
        return


    def check_supplier_xml(self):
        """
        REVISA SI ES FACTURA DE PROVEEDOR
        REVISA SI TIENE QUE VALIDAR XML O NO
        """
        for rec in self:
            country_mx = rec.env.ref('base.mx')
            if rec.move_type == "in_invoice" and rec.partner_id.commercial_partner_id.country_id == country_mx:
                if not rec.no_validate_xml:
                    rec.check_duplicate_uuid()
                    rec.validate_supplier_xml()
        return


    def check_duplicate_uuid(self):
        """
        verifica que no exista otra factura no cancelada
        con el mismo uuid
        """
        self.ensure_one()
        # uuid = self.get_xml_uuid()
        uuid = self.supplier_uuid
        if not uuid:
            raise ValidationError("El xml adjunto no contiene un UUID!")
        # buscar facturas con mismo uuid
        domain = [
            ('state','not in',('cancel','draft')),
            ('supplier_uuid','=',uuid),
            ('id','!=',self.id)
        ]
        res = self.search(domain)
        if res:
            print('res: ',res)
            raise ValidationError("""Se encontro el mismo UUID en la(s) siguiente(s) Factura(s):
{}
""".format('\n'.join(res.mapped('name')))
            )
        return True


    def get_xml_uuid(self):
        """
        extrae el uuid del xml adjunto
        """
        self.ensure_one()

        def get_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, 'Complemento'):
                node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        attachment_id = self.retrieve_supplier_xml_attachments()
        if not attachment_id:
            if self._context.get('compute'): # cuando se ejecuta desde metodo computado devolver Falso
                return False
            raise ValidationError('No se encontro ningun archivo XML adjunto a esta factura!')

        try:
            xml = base64.decodebytes(attachment_id.datas)
            xml = xmltodict.parse(xml)

            root = xml['cfdi:Comprobante']
            complemento = root['cfdi:Complemento']
            timbre = complemento["tfd:TimbreFiscalDigital"]
            uuid = timbre['@UUID']
            return uuid
        except Exception as e:
            return False

        

