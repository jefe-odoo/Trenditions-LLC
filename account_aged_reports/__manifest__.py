{
    'name': "account_aged",
    'summary': """
        Accounting Reports based on Dates (Invoice / Bill Date)""",
    'description': """
        Task: 2647913
        Aged Payable and Aged Receivable reports are age based on invoice date rather than the due date
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
    'data': [
        'data/account_financial_report_data.xml',
    ],
}