# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    edi_status = fields.Selection(selection=[
                                    ('draft', 'Draft'),
                                    ('pending', 'Pending'),
                                    ('sent', 'Sent'),
                                    ('fail', 'Failed')
                                ], string='EDI Status', default='draft', copy=False)
    edi_date = fields.Datetime(string='EDI Document Date')

    def export_invoice_to_edi(self):
        invoices = self
        sync_document_type = self.env['sync.document.type']
        sync_action = self.env['edi.sync.action'].search([('doc_type_id.doc_code', '=', 'export_invoice_flat')], limit=1)
        if not sync_action:
            raise UserError(_('Edi synchronization action not found'))
        try:
            values = {
                    'company_id': sync_action.config_id.company_id
                }
            conn = sync_action.config_id._get_provider_connection()
            sync_document_type.export_invoice_flat(conn, sync_action, values, invoices)
        except Exception as e:
            raise UserError(e)
        return True
