from odoo import models, fields, api


class ProductHealthRegisterConfig(models.TransientModel):
    """
    Class to handel health register configuration wizard
    """
    _name = 'product.health.register.config'
    _description = "Product Health Register Configuration Wizard"

    product_health_register_id = fields.Many2one('product.health.register', string="Health Register")
    product_ids = fields.Many2many('product.template')

    @api.onchange('product_health_register_id')
    def onchange_health_register_id(self):
        """
        onechange of product_health_register_id
        @return: -
        """
        #set the brand into wizard
        self.write({
            'product_ids': [(6, 0, self.product_health_register_id.product_ids.ids)]
        })

    def config_health_register_product(self):
        """
        unset if any and set to the select : configure health register to product
        @return: Boolean
        """
        #unset if any and set to the select
        if self.product_health_register_id:
            self.product_health_register_id.product_ids.write({'product_health_register_id': False})
            self.product_ids.write({'product_health_register_id': self.product_health_register_id, 'require_health_register': True})
        return True
