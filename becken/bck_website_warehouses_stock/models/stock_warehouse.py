# -*- coding: utf-8 -*-

from odoo import fields, models


class BckWarehouse(models.Model):
  _inherit = "stock.warehouse"

  website_active = fields.Boolean('Website available', default=False)