# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools, _
from odoo.tools.xml_utils import _check_with_xsd
from odoo.exceptions import UserError, ValidationError, Warning

import logging
import base64
from lxml import etree
from lxml.objectify import fromstring
from datetime import datetime
from io import BytesIO, StringIO
from suds.client import Client
from json.decoder import JSONDecodeError
import xml.etree.ElementTree as ET


_logger = logging.getLogger(__name__)


class AccountEdiFormatProdigia(models.Model):
    _inherit = "account.edi.format"

    def _l10n_mx_edi_get_prodigia_credentials(self, move):

        if not move.company_id.l10n_mx_edi_pac_username or not move.company_id.l10n_mx_edi_pac_password:
            return {
                'errors': [_("The username and/or password are missing.")]
            }

        return {
            'username': move.company_id.l10n_mx_edi_pac_username,
            'password': move.company_id.l10n_mx_edi_pac_password,
            'test': move.company_id.l10n_mx_edi_pac_test_env,
            'contract': move.company_id.l10n_mx_edi_pac_contract,
            'sign_url': 'http://timbrado.pade.mx:80/servicio/Timbrado4.0?wsdl',
            'cancel_url': 'http://timbrado.pade.mx:80/servicio/Timbrado4.0?wsdl',

        }

    def _l10n_mx_edi_prodigia_sign(self, move, credentials, cfdi):
        try:
            base64_bytes = base64.b64encode(cfdi)
            cfdi = base64_bytes.decode('utf-8')

            client = Client(credentials['sign_url'], timeout=500)
            if(credentials['test']):
                print("cfdi al tratar de timbrar: ", cfdi)
                response = client.service.timbradoBase64Prueba(
                    credentials['contract'], credentials['username'], credentials['password'], cfdi)
            else:
                # raise ValidationError('No deberia entrar aqui')
                response = client.service.timbradoBase64(
                    credentials['contract'], credentials['username'], credentials['password'], cfdi, ["REGRESAR_CON_ERROR_307_XML"])

            if response:
                xml = ET.fromstring(response)
                code = xml.find("./codigo").text
                timbrado = xml.find("./timbradoOk").text

                _logger.info("codigo: " + code)
                _logger.info("codigo: " + timbrado)

                if timbrado == 'true':
                    _logger.info("Entra aqui: ")
                    _logger.info(response)
                    xml_signed = xml.find("./xmlBase64").text or None
                    xml_signed2 = bytes(xml_signed, 'utf-8')
                    message_bytes = base64.b64decode(xml_signed2)
                    _logger.info("xml base 64: " + xml_signed)
                    if xml_signed:
                        return {
                            'cfdi_signed': message_bytes,
                            'cfdi_encoding': 'str'
                        }
                    else:
                        mensaje = xml.find('./mensaje').text
                        errors = []
                        if code:
                            errors.append(_("Code : %s") % code)
                        if mensaje:
                            errors.append(_("Message : %s") % mensaje)
                        return {'errors': errors}
                else:

                    if code == '307':
                        _logger.info(response)
                        xml_signed = xml.find("./xmlBase64").text or None
                        xml_signed2 = bytes(xml_signed, 'utf-8')
                        message_bytes = base64.b64decode(xml_signed2)
                        if xml_signed:
                            return {
                                'cfdi_signed': message_bytes,
                                'cfdi_encoding': 'str'
                            }
                    else:
                        mensaje = xml.find('./mensaje').text
                        errors = []
                        if code:
                            errors.append(_("Code : %s") % code)
                        if mensaje:
                            errors.append(_("Message : %s") % mensaje)
                        return {'errors': errors}

        except Exception as e:
            return {
                'errors': [_("The prodigia service failed to sign with the following error: %s", str(e))],
            }

    def _l10n_mx_edi_prodigia_cancel(self, move, credentials, cfdi):
        uuid = move.l10n_mx_edi_cfdi_uuid
        certificates = move.company_id.l10n_mx_edi_certificate_ids
        certificate = certificates.sudo().get_valid_certificate()
        cer_pem = certificate.get_pem_cer(certificate.content)
        key_pem = certificate.get_pem_key(
            certificate.key, certificate.password)
        try:

            username = credentials['username']
            password = credentials['password']
            contract = credentials['contract']
            test = credentials['test']
            rfc_receptor = move.partner_id.vat
            rfc_emisor = move.company_id
            cer_pem = base64.encodestring(cer_pem).decode('UTF-8')
            key_pem = base64.encodestring(key_pem).decode('UTF-8')

            uuids = []
            rfc_receptor = move.partner_id
            rfc_rec = ""
            if rfc_receptor.vat is False:
                raise Exception("El RFC del receptor no se encuentra.")
            else:
                rfc_rec = rfc_receptor.vat

            monto = f"{move.l10n_mx_edi_cfdi_amount or 0:.6f}"
            motivo = move.l10n_mx_motivo_cancelacion

            uuid_susitituto = move.l10n_mx_uuid_sustituto

            if move.move_type == 'entry':
                motivo = move.payment_id.l10n_mx_motivo_cancelacion
                monto = f"{0 :.6f}"
                uuid_susitituto = move.payment_id.l10n_mx_uuid_sustituto

            # raise Exception("el valor de motivo es: " + motivo)

            if motivo != "none":
                if motivo == "01":
                    if uuid_susitituto == "":
                        raise Exception(
                            "El uuid no puede ir vacio en caso de tener relacion")

                    uuids = [uuid+"|"+rfc_rec +
                             "|"+rfc_emisor.vat+"|" + str(monto) + "|" + motivo + "|" + uuid_susitituto]
                    _logger.info(uuid+"|"+rfc_rec + "|"+rfc_emisor.vat+"|" +
                                 str(monto) + "|" + motivo + "|" + uuid_susitituto)
                else:
                    uuids = [uuid+"|"+rfc_rec +
                             "|"+rfc_emisor.vat+"|" + str(monto) + "|" + motivo]

                    _logger.info("el valor de UUIDS es: " + str(uuids))

                cancelled = False
                if uuids != []:
                    if(test):
                        client = Client(credentials['cancel_url'], timeout=500)
                        response = client.service.cancelarConOpciones(
                            contract, username, password, rfc_emisor.vat, uuids, cer_pem, key_pem, certificate.password, ["MODO_PRUEBA:3"])

                    else:
                        client = Client(credentials['cancel_url'], timeout=500)
                        response = client.service.cancelar(
                            contract, username, password, rfc_emisor.vat, uuids, cer_pem, key_pem, certificate.password)
                else:
                    raise Exception("Error al armar la cadena de cancelación.")
            else:
                raise Exception(
                    "No puedes cancelar un CFDI sin motivo de cancelación")
        except Exception as e:
            return {
                'errors': [_("El servicio de cancelaciones de prodigia fallo por el siguiente error: %s", str(e))],
            }
        if response:
            xml = ET.fromstring(response)
            statusOk = xml.find("./statusOk").text
            if(statusOk == 'true'):
                uuid_request = xml.find(
                    './cancelaciones').find("./cancelacion")
                code = uuid_request.find("./codigo").text
                msg = uuid_request.find("./mensaje").text
                cancelled = code in ('201', '202')
                msg = '' if cancelled else msg
                code = '' if cancelled else code
            else:
                cancelled = False
                msg = xml.find("./mensaje").text
                code = xml.find("./codigo").value

            errors = []
            if code:
                errors.append(_("Code : %s") % code)
            if msg:
                errors.append(_("Message : %s") % msg)
            if errors:
                return {'errors': errors}

            if cancelled:
                return {'success': True}
            else:
                return {'success': False, 'errors': errors}
        else:
            errors = []
            errors.append(_("Code : %s") % '999')
            errors.append(_("Message : %s") % 'El Servidor no responde')
            if errors:
                return {'errors': errors}

    def _l10n_mx_edi_prodigia_sign_invoice(self, invoice, credentials, cfdi):
        return self._l10n_mx_edi_prodigia_sign(invoice, credentials, cfdi)

    def _l10n_mx_edi_prodigia_cancel_invoice(self, invoice, credentials, cfdi):
        return self._l10n_mx_edi_prodigia_cancel(invoice, credentials, cfdi)

    def _l10n_mx_edi_prodigia_sign_payment(self, move, credentials, cfdi):
        return self._l10n_mx_edi_prodigia_sign(move, credentials, cfdi)

    def _l10n_mx_edi_prodigia_cancel_payment(self, move, credentials, cfdi):
        return self._l10n_mx_edi_prodigia_cancel(move, credentials, cfdi)
