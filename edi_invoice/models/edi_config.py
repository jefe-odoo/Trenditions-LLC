# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
import pprint
import logging
import xlwt
import csv

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)
EDI_DATE_FORMAT = '%m/%d/%Y'


class SyncDocumentType(models.Model):

    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
                                ('export_invoice_flat', '810 - Export Invoice (TrueCommerce Flatfile)'),
                                ])
    segment_terminator = fields.Char(string='Segment Terminator',
                        help='Symbol representing segment terminator delimiter, Industry practice: return/linefeed (\\r\\n")',
                        default='\\r\\n'
                                     )
    data_ele_separator = fields.Char(string='Data Element Separator',
                        help='Symbol representing data element separator. Industry practice : asterisk (*), tilde (~)',
                        default='*'
                                     )
    component_ele_separator = fields.Char(string='Component Element Separator',
                        help='Symbol representing Component element separator. Industry practice : colon (:)',
                        default=':'
                                          )

    def _do_export_po(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        _logger.info('Not Implemented')

        return True

    def make_invoice_line_flatfile_data(self, invoice):
        # join_seg_ele = '%s' % (self.segment_terminator)
        # join_data_ele = '%s' % (self.data_ele_separator)
        invoice_line_element = []
        line_count = 1
        for line in invoice.invoice_line_ids:
            line_data_elements = [
                "I",
                line_count,
                line.product_id.default_code or '',
                line.product_id.default_code or '',
                line.product_id.barcode or '',
                line.name,
                line.quantity,
                line.product_uom_id.name or '',
                line.price_unit,
                sum(line.mapped('sale_line_ids.product_uom_qty')) or line.quantity,
                0,  # Number of packs in unit
                0,  # Number of inner packs within the master pack
                0,  # Line item allowance percentage
                0,  # Line item allowance dollar amount
            ]
            # line_data = join_data_ele.join([str(el) for el in line_data_elements])
            # line_data = '%s' % (line_data)
            invoice_line_element.append(line_data_elements)
            line_count = line_count + 1
        # invoice_lines = join_seg_ele.join(invoice_line_element)
        return invoice_line_element

    def make_invoice_x12_flatfile_data(self, invoice):
        order = invoice.invoice_line_ids.mapped('sale_line_ids.order_id')
        order_id = order[0] if order else False
        # join_seg_ele = '%s' % (self.segment_terminator)
        # join_data_ele = '%s' % (self.data_ele_separator)
        header_data_elements = [
            'H', '810',
            invoice.partner_id.id,
            invoice.name,
            invoice.invoice_date and invoice.invoice_date.strftime(EDI_DATE_FORMAT) or '',
            order_id.name if order_id else '',
            order_id.date_order.strftime(EDI_DATE_FORMAT) if order_id else '',
            '',  # Bill of Lading
            '',  # Carrier Pro
            '',  # SCAC
            order.carrier_id.name if (order_id and order.carrier_id) else '',
            invoice.partner_shipping_id.name,
            invoice.partner_shipping_id.street or '',
            invoice.partner_shipping_id.street2 or '',
            invoice.partner_shipping_id.city or '',
            invoice.partner_shipping_id.state_id.name or '',
            invoice.partner_shipping_id.zip or '',
            invoice.partner_shipping_id.country_id.name or '',
            '',  # The Ship To Code - The Store# where the product is shipping to
            invoice.partner_id.name,
            invoice.partner_id.street or '',
            invoice.partner_id.street2 or '',
            invoice.partner_id.city or '',
            invoice.partner_id.state_id.name or '',
            invoice.partner_id.zip or '',
            invoice.partner_id.country_id.name or '',
            '',  # Bill to Code
            '',  # Ship Date
            invoice.invoice_payment_term_id .name or '',
            (invoice.invoice_date_due - invoice.invoice_date).days if invoice.invoice_date and invoice.invoice_date_due else 0,
            0,  # Discount Days Due
            0,  # Discount Percent
            '',  # Note
            0,  # Weight
            0,  # Total Cases Shipped
            invoice.amount_tax,
            invoice.amount_total,
            0,  # Charge Amount2
            0,  # Allowance Percent1
            0,  # Allowance Amount1
            0,  # Allowance Percent2
            0,  # Allowance Amount2
        ]

        # final_row_data = [
        #     join_data_ele.join([str(ex) for ex in header_data_elements]),
        # ]
        # invoice_data = join_data_ele.join(final_row_data)
        # invoice_data = '%s' % (invoice_data)
        invoice_lines = self.make_invoice_line_flatfile_data(invoice)
        flat_invoice = [header_data_elements] + [i for i in invoice_lines]
        return flat_invoice

    def _do_export_invoice_flat(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        if 'active' in values and not values.get('active'):
            return False
        # get invoices to be sent to edi

        invoices = self.env['account.move'].search([('state', '=', 'posted'), ('type', '=', 'out_invoice'), ('edi_status', 'in', ('pending', 'fail', 'draft'))], limit=20)
        return self.export_invoice_flat(conn, sync_action_id, values, invoices)

    @api.model
    def export_invoice_flat(self, conn, sync_action_id, values, invoices):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        conn._connect()
        conn.cd(sync_action_id.dir_path)
        # get invoices to be sent to edi
        if invoices:
            for invoice in invoices:
                invoice_data = self.make_invoice_x12_flatfile_data(invoice)
                # Specifying column
                if invoice_data:
                    filename = 'invoice_info_%s.csv' % invoice.name.replace('/', '_')
                    csv.register_dialect('myDialect', delimiter=',')
                    with open(filename, 'w', newline='') as file:
                        writer = csv.writer(file, dialect='myDialect')
                        writer.writerows(invoice_data)
                    # TODO : used upload method of sftp
                    filename = filename.strip()
                    try:
                        with open(filename, 'rb') as file:
                            conn.upload_file(filename, file)
                            file.close()
                        # Update EDI Status to sent
                        invoice.write({'edi_status': 'sent', 'edi_date': fields.Datetime.now()})
                        invoice.sudo().message_post(body=_('Invoice file created on the EDI server %s' % filename))
                        _logger.info('Invoice file created on the server path of %s/%s' % (sync_action_id.dir_path, filename))
                    except Exception as e:
                        invoice.write({'edi_status': 'fail'})
                        _logger.error("file not uploaded %s" % e)
                    os.remove(filename)
                self.flush()
        conn._disconnect()
        return True
