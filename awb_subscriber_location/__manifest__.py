# -*- coding: utf-8 -*-
##############################################################################
#
#   ACHIEVE WITHOUT BORDERS
#
##############################################################################
{
    'name': "AWB Subscriber Location",

    'summary': """
        Subscriber's Location Module.
        """,

    'description': """
        Extension Odoo Apps
    """,

    'author': "Achieve Without Borders",

    'license': 'LGPL-3',

    'category': 'Localization',

    'version': '13.0.1.0.0',

    'depends': ['account_accountant', 'base_address_city', 'contacts', 'mail', 'project', 'sale_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/project_view.xml',
        'views/res_city_view.xml',
        'views/res_partner_view.xml',
        'views/sale_view.xml',
        'views/subscriber_location_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False

}
