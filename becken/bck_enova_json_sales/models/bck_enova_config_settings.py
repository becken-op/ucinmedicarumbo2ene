# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enova_server = fields.Char(string='Server uri', readonly=False, config_parameter='bck_enova_json_sales.enova_server')
    enova_user = fields.Char(string='Ftp username', readonly=False, config_parameter='bck_enova_json_sales.enova_user')
    enova_password = fields.Char(string='Ftp password', readonly=False, config_parameter='bck_enova_json_sales.enova_password')
    enova_in_path = fields.Char(string='Path to search quotations', readonly=False, config_parameter='bck_enova_json_sales.enova_in_path')
    enova_out_path = fields.Char(string='Path to store processed quotations', readonly=False, config_parameter='bck_enova_json_sales.enova_out_path')
    enova_processed_path = fields.Char(string='Path to backup processed quotations', readonly=False, config_parameter='bck_enova_json_sales.enova_processed_path')




