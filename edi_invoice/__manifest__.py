# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'EDI Invoicing',
    'version': '1.0',
    'category': 'Tools',
    'description': """
Allows Exporting EDI Invoices to True Commerce
==============================================================
EDI Sale Import/Export (850)
""",
    'depends': ['base_edi', 'account'],
    'data': [
        'data/edi_invoice_data.xml',
        'views/account_move_views.xml',
        'views/edi_config_view.xml',
    ],
    'demo': [],
    'installable': True,
}
