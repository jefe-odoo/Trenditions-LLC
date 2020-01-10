# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'EDI Sale',
    'version': '1.0',
    'category': 'Tools',
    'description': """
Allows Exporting EDI Purchase to True Commerce
==============================================
EDI Purchase Import/Export (850)
""",
    'depends': ['base_edi', 'sale_management'],
    'data': [
        'data/edi_sale_data.xml',
        'views/sale_views.xml',
    ],
    'demo': [],
    'installable': True,
}
