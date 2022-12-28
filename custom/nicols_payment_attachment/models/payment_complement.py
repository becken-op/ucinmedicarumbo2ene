from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from suds.client import Client
import random
import base64
from lxml import etree
from lxml.objectify import fromstring
import xmltodict


class PaymentComplement(models.Model):
    _inherit = 'account.payment'

    complement_payment_uuid = fields.Char(string='Complemento UUID')
    complement_payment_validated = fields.Boolean(
        string='Complemento Validado', default=False)
    complement_payment_status = fields.Char(string='Complemento Estado')


    def _get_uuid_from_attachment(self, attachment_id):
        xml = base64.decodebytes(attachment_id.datas)
        xml = xmltodict.parse(xml)

        root = xml['cfdi:Comprobante']
        complemento = root['cfdi:Complemento']
        timbre = complemento.get("tfd:TimbreFiscalDigital")
        uuid = timbre and timbre['@UUID'] or ""

        emisor = root.get('cfdi:Emisor')
        emisor_rfc = emisor and emisor['@Rfc'] or ""

        receptor = root.get('cfdi:Receptor')
        receptor_rfc = receptor and receptor['@Rfc'] or ""

        total = root.get('@Total') or 0

        pagos = complemento.get('pago10:Pagos') and complemento['pago10:Pagos'].get('pago10:Pago') or False
        if isinstance(pagos, list):
            total = 0
            for pago in pagos:
                total += float(pago.get('@Monto', 0))
        elif pagos:
            total = pagos['@Monto']
        return uuid, emisor_rfc, receptor_rfc, total

    def check_status_sat(self, emisor, receptor, total, uuid):
        try:
            company = self.company_id or self.env.user.company_id
            contract = company.l10n_mx_edi_pac_contract
            password = company.l10n_mx_edi_pac_password
            user = company.l10n_mx_edi_pac_username
            url = 'https://timbrado.pade.mx/odoo/PadeOdooTimbradoService?wsdl'
            rfc_emisor = emisor
            rfc_receptor = receptor
            total = total
            uuid = uuid
            client = Client(url, timeout=20)
            check = client.service.consultarEstatusComprobante(
                contract, user, password, uuid, rfc_emisor, rfc_receptor, total, [''])
            estado = getattr(check, 'estado', None)
            if not estado:
                check = client.service.consultarEstatusComprobante(
                    contract, user, password, uuid, rfc_emisor, rfc_receptor, total, [''])
                estado = getattr(check, 'estado', None)
            return estado
        except Exception as e:
            raise UserError(
                "Error al verificar el estatus de la factura: " + str(e))

    def check_payment_is_valid(self, emisor, receptor, total):
        company = self.company_id or self.env.user.company_id
        rfc_emisor = self.partner_id and self.partner_id.vat or ''
        rfc_receptor = company.vat
        total_payment = self.amount
        if(not rfc_emisor or rfc_emisor != emisor):
            raise UserError("No coincide el xml con el pago en el campo Rfc del emisor: " +
                            str(emisor) + " y en el pago de odoo es " + str(rfc_emisor))

        if(rfc_receptor != receptor):
            raise UserError("No coincide el xml con el pago en el campo Rfc del receptor: " +
                            str(receptor) + " y en el pago de odoo es " + str(rfc_receptor))

        if(total_payment != float(total)):
            raise UserError("No coincide el xml con el pago en el campo Monto pagado: " +
                            str(total) + " y en el pago de odoo es " + str(total_payment))

    def payment_attachment_copy(self):
        attach = self.env['ir.attachment'].search(
            ['&', ('res_id', '=', self.id), ('res_model', '=', 'account.payment')])
        if attach:
            for a in attach:
                if ".xml" in a.name:
                    uuid, emisor, receptor, total = self._get_uuid_from_attachment(a)
                    self.check_payment_is_valid(emisor, receptor, total)
                    estado = self.check_status_sat(
                        emisor, receptor, '0', uuid)
                    print("estado: ",estado)
                    self.complement_payment_status = estado
                    self.complement_payment_uuid = uuid
                    self.complement_payment_validated = estado
        else:
            self.complement_payment_uuid = ""

    def send_email_complement_payment(self):
        for pago in self:
            template = self.env.ref('account.mail_template_data_payment_receipt', False)
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                default_model='account.payment',
                default_res_id=pago.id,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='comment',
                force_email=True
            )
            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
            }
