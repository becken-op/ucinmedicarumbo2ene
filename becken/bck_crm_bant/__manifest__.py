# -*- coding: utf-8 -*-
{
    'name': "BANT - Cálculo de criterios en oportunidades",

    'summary': """
    Realiza el cálculo de oportunidades BANT en base a información extra agregada a las oportunidades""",

    'description': """
    """,

    'author': 'Becken',
    'support': 'jose.candelas@becken.com',
    'license': 'OPL-1',
    'website': 'http://www.becken.mx',
    'currency': 'USD',
    'price': 139.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    'category': 'CRM',
    'version': '14.0.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 'crm', 'product', 'sale', 'hr', 'utm',
        'account', 'stock', 'sale_stock', 'delivery',
        'product_expiry', 'sale_crm', 'sale_margin',
        'bi_advance_hide_show_menu'],

    # always loaded
    'data': [
        'security/crm_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/crm_lead_views.xml',
        'views/menu_crm_bant.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/product_template_views.xml',
        'views/stock_production_lot_views.xml',
        'views/sale_order_type_views.xml',
        'views/stock_move_views.xml',
        'views/inherit_purchaseorder_report.xml',
        'data/ir_cron_data.xml',
        'data/bant_data.xml',
        'data/opportunity_data.xml',
        'data/sale_order_type_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# TODO:
# Con respecto a lo de Generar una actividad planificada cuando la oportunidad tiene una calificación menor a 40%
# (A que usuarios se les debe notificar->
# Lo ideal sería avisarle al jefe directo y a director de Marketing para que analicen esa oportunidad)
