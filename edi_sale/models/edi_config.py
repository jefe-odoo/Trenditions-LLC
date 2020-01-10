# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
import pprint
import logging
import tempfile
import xlwt
import xlrd

from odoo import fields, models

_logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)
EDI_DATE_FORMAT = '%m/%d/%Y'


class SyncDocumentType(models.Model):

    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
                                ('import_so_flat', '850 - Import Order (TrueCommerce Flatfile)'),
                                ])

    def make_order_line_flatfile_data(self, order):
        # join_seg_ele = '%s' % (self.segment_terminator)
        # join_data_ele = '%s' % (self.data_ele_separator)
        order_line_element = []
        line_count = 1
        for line in order.order_line:
            line_data_elements = [
                "I",
                line_count,  # Row ID
                line.id,  # Line
                line.product_id.default_code or '',  # Vendor Part
                line.product_id.default_code or '',  # Buyer Part
                '',  # UPC
                line.name,  # Description
                line.product_qty,  # Quantity
                line.product_uom.name or '',  # UOM
                line.price_unit,  # Unit Price
                '',  # Pack Size
                '',  # # of Inner Packs
                '',  # Item Allowance Percent1
                '',  # Item Allowance Amount1
            ]
            # line_data = join_data_ele.join([str(el) for el in line_data_elements])
            # line_data = '%s' % (line_data)
            order_line_element.append(line_data_elements)
            line_count = line_count + 1
        # invoice_lines = join_seg_ele.join(invoice_line_element)
        return order_line_element

    def make_purchase_x12_flatfile_data(self, order):
        flat_order = []
        invoice = order and order.invoice_ids and order.invoice_ids[0] or False
        if order:
            header_data_elements = [
                'H', '850',
                order.id,  # Transaction ID
                order.id,  # Accounting ID
                order.name,  # Purchase Order Number
                order.date_approve.strftime(EDI_DATE_FORMAT) or '',  # PO Date
                invoice and invoice.partner_shipping_id and invoice.partner_shipping_id.name or '',  # Ship To Name
                invoice and invoice.partner_shipping_id and invoice.partner_shipping_id.street or '',  # Ship To Address - Line One
                invoice and invoice.partner_shipping_id and invoice.partner_shipping_id.street2 or '',  # Ship To Address - Line Two
                invoice and invoice.partner_shipping_id and invoice.partner_shipping_id.city or '',  # Ship To City
                invoice and invoice.partner_shipping_id and invoice.partner_shipping_id.state_id.name or '',  # Ship To State
                invoice and invoice.partner_shipping_id and invoice.partner_shipping_id.zip or '',  # Ship To Zip code
                invoice and invoice.partner_shipping_id and invoice.partner_shipping_id.country_id.name or '',  # Ship To Country
                '',  # Store #
                '',  # The Ship To Code - The Store# where the product is shipping to
                order.partner_id.name or '',  # Bill To Name
                order.partner_id.street or '',  # Bill To Address - Line One
                order.partner_id.street2 or '',  # Bill To Address - Line Two
                order.partner_id.city or '',  # Bill To City
                order.partner_id.state_id.name or '',  # Bill To State
                order.partner_id.zip or '',  # Bill To Zip code
                order.partner_id.country_id.name or '',  # Bill To Country
                '',  # Bill To Code
                '',  # Ship Via
                order.date_approve.strftime(EDI_DATE_FORMAT),  # Ship Date
                '',  # Terms
                '',  # Note
                '',  # Department Number
                '',  # Cancel Date
                '',  # Do Not Ship Before
                '',  # Do Not Ship After
                '',  # Allowance Percent1
                '',  # Allowance Amount1
                '',  # Allowance Percent2
                '',  # Allowance Amount2
            ]
            order_lines = self.make_order_line_flatfile_data(order)
            flat_order = [header_data_elements] + [i for i in order_lines]
        return flat_order

    def _do_import_so_flat(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        conn._connect()
        conn.cd(sync_action_id.dir_path)
        # get sale order to be sent to edi
        orders = self.env['sale.order'].search([('state', '=', 'purchase'), ('edi_status', 'in', ('pending', 'fail', 'draft'))])
        if orders:
            for order in orders:
                order_data = self.make_purchase_x12_flatfile_data(order)
                workbook = xlwt.Workbook()
                sheet = workbook.add_sheet(order.name)
                # Specifying column
                if order_data:
                    row = 0
                    for values in order_data:
                        for v in range(0, len(values)):
                            sheet.write(row, v, str(values[v]))
                        row += 1
                    workbook.save("purchase_order_%s.xls" % order.name.replace('/', '_'))
                    # TODO : used upload method of sftp
                    filename = 'purchase_order_%s.xls' % order.name.replace('/', '_')
                    filename = filename.strip()
                    try:
                        with open(filename, 'rb') as file:
                            conn.upload_file(filename, file)
                            file.close()
                            conn._conn.quit()
                        # Update EDI Status to sent
                        order.write({'edi_status': 'sent'})
                    except Exception as e:
                        order.write({'edi_status': 'fail'})
                        _logger.error("filename>>>>>>>>>>>>>>%s" % e)
                    os.remove(filename)
        return True
