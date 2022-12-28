# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    classification = fields.Selection([
            ('commodity', 'Commodity'),
            ('differentiate', 'Differentiate'),
        ],
        string='Classification',
        help=''
    )
    specialty = fields.Selection([
            ('Terapia Respiratoria', 'Terapia Respiratoria'),
            ('Anestesia', 'Anestesia'),
            ('Neonatología', 'Neonatología'),
            ('Vía Aérea', 'Vía Aérea'),
            ('Otros', 'Otros'),
        ],
        string='Specialty',
        help=''
    )
    basic_chart = fields.Char('Basic Chart')
    quality_management_system = fields.Boolean(
        string='SGC',
        default=False,
        help='Sistema de Gestión de Calidad',
        store=True)
    product_family = fields.Selection([
            ('BCPAP', 'BCPAP'),
            ('CTO CONV NEO', 'CTO CONV NEO'),
            ('CTO REUS', 'CTO REUS'),
            ('DRENAJE TORACICO', 'DRENAJE TORACICO'),
            ('EVAQUA ADULT', 'EVAQUA ADULT'),
            ('EVAQUA NEO', 'EVAQUA NEO'),
            ('HIGIENE PULMONAR', 'HIGIENE PULMONAR'),
            ('HUMIDIFCACION', 'HUMIDIFCACION'),
            ('MASCARILLA LARINGEA', 'MASCARILLA LARINGEA'),
            ('MR850', 'MR850'),
            ('NEOPUFF', 'NEOPUFF'),
            ('NIV MASKS', 'NIV MASKS'),
            ('OPTIFLOW', 'OPTIFLOW'),
            ('OPTIFLOW JR', 'OPTIFLOW JR'),
            ('RESUSCITACION', 'RESUSCITACION'),
            ('TERAPIA DE OXIGENO', 'TERAPIA DE OXIGENO'),
            ('TRAQUEOSTOMIA', 'TRAQUEOSTOMIA'),
            ('VIA AEREA', 'VIA AEREA'),
        ],
        string='Family',
        help=''
    )
    campaign_id = fields.Many2one('utm.campaign',
        string='Campaign',
        help='')
    patient = fields.Selection([
            ('ADULTO', 'ADULTO'),
            ('GENERAL', 'GENERAL'),
            ('NEONATAL', 'NEONATAL'),
            ('PEDIATRICO', 'PEDIATRICO'),
        ],
        string='Patient',
        help=''
    )
    product_type = fields.Selection([
        ('ACCESORIO', 'ACCESORIO'),
        ('CONSUMIBLE', 'CONSUMIBLE'),
        ('EQUIPO', 'EQUIPO'),
        ],
        string='Type',
        help=''
    )
