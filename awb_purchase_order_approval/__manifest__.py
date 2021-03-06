# -*- coding: utf-8 -*-
##############################################################################
#
#   ACHIEVE WITHOUT BORDERS
#
##############################################################################
{
    'name': "AWB Purchase Order Approval",
    'summary': """
        AWB Purchase Order Approval
        """,
    'description': """
        AWB Purchase Order Approval
    """,
    'author': "Achieve Without Borders, Inc",
    'website': "http://www.achievewithoutborders.com",
    'category': "Operations/Purchase",
    'version': '13.0.1.0.0',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_approval_views.xml',
        'views/purchase_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
