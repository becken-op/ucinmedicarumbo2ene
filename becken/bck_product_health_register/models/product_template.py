#-*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_health_register_id = fields.Many2one(
        'product.health.register',
        string="Health Register")
    require_health_register = fields.Boolean('Require Health Register')

    @api.onchange('require_health_register')
    def _onchange_require_health_register(self):
        for product_template_id in self:
            if not product_template_id.require_health_register:
                product_template_id.product_health_register_id = False

