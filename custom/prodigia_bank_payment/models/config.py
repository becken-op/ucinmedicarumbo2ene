# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo import api, exceptions, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError

"""
Se establece moneda de grupo de pagos
Si se selecciona una, esta sera usada como la moneda por defecto
para todos los pagos generados automaticamente por el modelo
de grupo de pagos
"""

class ResCompany(models.Model):
    _inherit = 'res.company'


    force_payment_group_currency_id = fields.Many2one('res.currency',
        required=False,
        readonly=False,
        string='Moneda de grupos de pago bancario',
        help="Si se seleccoina una moneda, esta se usara para todos los pagos creados en el modulo de pagos bancarios")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


     force_payment_group_currency_id = fields.Many2one('res.currency',
        related="company_id.force_payment_group_currency_id",
        required=False,
        readonly=False,
        string='Moneda de grupos de pago bancario',
        help="Si se seleccoina una moneda, esta se usara para todos los pagos creados en el modulo de pagos bancarios")