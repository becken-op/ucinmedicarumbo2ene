from odoo import _, api, fields, models, tools


class AccountInvoice(models.Model):

    _inherit = 'account.move'

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
