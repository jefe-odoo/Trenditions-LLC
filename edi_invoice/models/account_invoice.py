# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    edi_status = fields.Selection(selection=[
                                    ('draft', 'Draft'),
                                    ('pending', 'Pending'),
                                    ('sent', 'Sent'),
                                    ('fail', 'Failed')
                                ], string='EDI Status', default='draft', copy=False)
    edi_date = fields.Datetime(string='EDI Document Date')
