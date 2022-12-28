# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

import xmltodict
from lxml.objectify import fromstring
import base64
import zipfile
import io


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'


    def unlink(self):
        """
        resetear campo uuid de proveedor en
        facturas
        """
        # se buscan extraen todos los adjuntos 
        # donde el modelo = account.move y
        # mimetipe = application/xml
        filtered_attachments = self.filtered(
            lambda m: m.mimetype == 'application/xml' and m.res_model == 'account.move')
        if filtered_attachments:
            move_ids = filtered_attachments.mapped('res_id')
            # se buscan los account.move correspondientes
            # y se filtran los que sean de tipo facturas de proveedor
            moves = self.env['account.move'].browse(move_ids)
            if moves:
                supplier_invoices = moves.filtered(
                    lambda m: m.move_type == 'in_invoice' and m.supplier_uuid)
                if supplier_invoices:
                    # se resetea uuid
                    supplier_invoices.write({'supplier_uuid': False})
                    # se recalcula con los otros adjuntos que tenga
                    supplier_invoices._compute_supplier_uuid()
        return super(IrAttachment, self).unlink()
