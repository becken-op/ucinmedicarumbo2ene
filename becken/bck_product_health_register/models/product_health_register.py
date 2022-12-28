#-*- coding: utf-8 -*-
from odoo import api, fields, models

class HealthRegister(models.Model):
    _name = 'product.health.register'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Product Health Register'

    name = fields.Char('Health Register', required=True, copy=False)
    active = fields.Boolean(string="Estado", default=True)
    # Vigente, En Renovación, Sin Renovación
    state = fields.Selection([
        ('valid', 'Valid'),
        ('under_renovation', 'Under Renovation'),
        ('no_renewal', 'No Renewal'),
        ], string='Status', readonly=False, copy=False, index=True, tracking=3, default='valid')
    due_date = fields.Date(string="Fecha Vencimiento", tracking=True)
    distinctive = fields.Char(string="Denominación Distintiva", tracking=True)
    generic = fields.Char(string="Denominación Genérica", tracking=True)
    manufacturer = fields.Char(string="Fabricado por", tracking=True)
    made_for = fields.Char(string="Fabricado para", tracking=True)
    manufactured_place = fields.Char(string="Fabricado en", tracking=True)
    actual_manufacturer = fields.Char(string="Dirección Fabricante Real", tracking=True)
    legal_manufacturer = fields.Char(string="Dirección Fabricante Legal", tracking=True)
    cautionary_legends = fields.Char(string="Leyendas Precautorias", tracking=True)
    product_ids = fields.One2many(
        'product.template', 'product_health_register_id', string="Health Register Products", readonly=True)
    products_count = fields.Integer(
        string='Number of products',
        compute='_compute_products_count',
        help='It shows the number of product counts',
    )

    @api.depends('product_ids')
    def _compute_products_count(self):
        """
        product count computation
        @return:
        """
        for health_register in self:
            health_register.products_count = len(health_register.product_ids)

    def set_health_register_wizard(self):
        """
        action health register wizard
        @return: wizard-action
        """
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.health.register.config',
            'name': "Product Health Register Configuration",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(default_product_health_register_id=self.id),
        }
        return action
