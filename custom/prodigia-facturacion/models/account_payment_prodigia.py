import base64
from itertools import groupby
import re
import logging
from datetime import datetime
from io import BytesIO

from lxml import etree
from lxml.objectify import fromstring
from suds.client import Client

from odoo import _, api, fields, models, tools
from odoo.tools.xml_utils import _check_with_xsd
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools import float_round
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_repr

CFDI_TEMPLATE = 'l10n_mx_edi.payment10'
CFDI_XSLT_CADENA = 'l10n_mx_edi/data/3.3/cadenaoriginal.xslt'
CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
}


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    l10n_mx_uuid_sustituto =  fields.Char(string="UUID Sustituto")
    l10n_mx_motivo_cancelacion = fields.Selection(
        selection=[
            ('none', "Seleccionar motivo de Cancelacion"),
            ('01', "Comprobante emitido con errores con relación"),
            ('02', "Comprobante emitido con errores sin relación"),
            ('03', "No se llevó a cabo la operación"),
            ('04', "Operación nominativa relacionada en la factura global"),
        ],
        string="Motivo de Cancelación", copy=False,
        default='none',
        help="Al cancelar un CFDI es necesario elegir cual es el motivo de la cancelacion apartir del 1 de enero del 2022.")
