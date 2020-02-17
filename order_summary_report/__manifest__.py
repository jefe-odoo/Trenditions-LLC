# -*- coding: utf-8 -*-
# ======================================================
#     @Author: KSOLVES India Private Limited
#     @Email: sales@ksolves.com
# ======================================================
{
    'name': "Trendition: Order Summary Report",
    'summary': """
        Prepares Order Summary Report 
        """,
    'description': """
    """,
    'author': "Ksolves India Pvt. Ltd.",
    'license': 'OPL-1',
    'website': "https://www.ksolves.com",
    'maintainer': 'Ksolves India Pvt. Ltd.',
    'live_test_url': '',
    'category': 'Stock',
    'version': '1.0.0',
    'support': 'sales@ksolves.com',
    'depends': ['base', 'stock', 'purchase', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'report/order_summary_report.xml',
        'wizard/order_summary_report_view.xml',
        'views/views.xml',

    ],

}
