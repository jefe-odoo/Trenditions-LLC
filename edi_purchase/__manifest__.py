# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'EDI Purchase',
    'version': '1.0',
    'category': 'Tools',
    'description': """
Allows Exporting EDI Purchase to True Commerce
==============================================================
EDI Purchase Import/Export (850)
""",
    'depends': ['base_edi', 'purchase'],
    'data': [
        'data/edi_purchase_data.xml',
        'views/purchase_views.xml',
    ],
    'demo': [],
    'installable': True,
}
