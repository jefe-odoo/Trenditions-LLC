{
    'name': "Aged Reports by Date",
    'summary': """
        Limit visibility to Sales Teams""",
    'description': """
        Task: 2647913
        The reports are age based on client's invoice date rather than the due date
    """,
    "author": "Odoo Inc",
    "website": "http://www.odoo.com",
    "category": "Custom Development",
    "license": "OEEL-1",
    "version": "0.1",
    'depends': [
        'account',
        'account_reports',
    ],
    # 'data': [
    #     # 'views/template_view.xml',
    #     'data/account_financial_report_data.xml',
    # ],
}
