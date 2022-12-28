# -*- coding: utf-8 -*-
{
    'name': 'Activity Geolocation',

    'summary': """
    This module tracks the user's geolocation when an Activity is marked as Done with customer distance restriction.""",
    

    'description': """
    a. Configure the maximum distance in meters accepted to mark as done activities between the Salesvendor and the Customer Location.
    b. Configure the Activity Types that use geolocation.
    c. Schedule an activity that use geolocation.
    d. Mark as done the activity, if is the first time that use geolocation, the navigator will ask you if you want to share your location to this site, please allow this and remember this decision.
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 169.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '14.0.1.1',
    # 14.0.1.1 Changelog
    # Add Settings

    # any module necessary for this one to work correctly
    'depends': ['crm', 'mail'],

    # always loaded
    'data': [
        'views/assets.xml',
        'views/res_partner_views.xml',
        'views/mail_activity_type_views.xml',
        'views/mail_message_views.xml',
        'views/res_config_settings_views.xml',
        'views/mail_activity_views.xml',
        'data/location_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
