# -*- coding: utf-8 -*-
{
    'name': 'CRM Bid Management',

    'summary': """
    This module allow to manage tenders from CRM app.""",

    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 399.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'CRM',
    'version': '14.0.1.0',
    # 14.0.1.1 Changelog
    # Add Settings

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'crm',
        'sale_crm',
        'purchase',
        'account_check_printing',
        'bck_crm_bant',
        'bck_product_health_register',
        'bck_product_brand_ept',
        'report_xlsx'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'report/sale_report.xml',
        'report/sale_report_templates.xml',
        'views/crm_lead_views.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'wizard/bid_line_authorization_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}

# Nombre y código en el pedido debe ser el del cliente, si tiene, soll en el PDF reporte
# Cliente obligatorio en Oportunidades ???
# Que relación tienen las status de la licitación con los status de las partidas
# Hacer el precio unitario no editable
# Quien decide si va a requerir autorización
# Qty Min Requested o Max, cual es la cantidad de la cotización