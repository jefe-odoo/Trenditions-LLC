# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    edi_status = fields.Selection(selection=[
                                    ('draft', 'Draft'),
                                    ('pending', 'Pending'),
                                    ('sent', 'Sent'),
                                    ('fail', 'Failed')
                                ], string='EDI Status', default='draft')
    edi_date = fields.Datetime(string='EDI Document Date')