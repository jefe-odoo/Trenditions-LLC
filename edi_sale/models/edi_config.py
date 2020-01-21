# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
import pprint
import logging
import csv


from odoo import fields, models

_logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)
EDI_DATE_FORMAT = '%m/%d/%Y'


class SyncDocumentType(models.Model):

    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
                                ('import_so_flat', '850 - Import Order (TrueCommerce Flatfile)'),
                                ])

    def prepared_order_line_from_flatfile(self, order, rows):
        order_line_data = []
        for row in rows:
            product = self.env['product.product'].search(['|', ('barcode', 'ilike', row[2]), ('default_code', 'ilike', row[3])], limit=1)
            uom = self.env['uom.uom'].search([('name', 'ilike', row[7])], limit=1)
            if product:
                line_data = {
                    'order_id': order.id,
                    # Row ID 10
                    # Line # 73111043938: barcode
                    'product_id': product and product.id,
                    # Vendor Part # 1353024 ??
                    # Buyer Part # 73111043938 :default_code
                    # UPC #
                    # Description: Hooey Rodeo Tooled Leather Wallet, Saddle Brown Tooling & Embossed Dark Green Lo
                    'name': row[5],
                    # Quantity 1
                    'product_uom_qty': row[6],
                    # UOM Each
                    'product_uom': uom and uom.id,
                    # Unit Price 26
                    'price_unit': row[8]
                    # Pack Size
                    # # of Inner Packs
                    # Item Allowance Percent1
                    # Item Allowance Amount1
                }
                order_line_data.append(line_data)
            else:
                print ('product not found---------------------', row[2])
        return order_line_data

    def prepared_order_from_flatfile(self, row):
        order = self.env['sale.order']
        if row and row[0] == 'H' and row[1] == '480':
            partner = self.env['res_partner'].search(['ref', '=', row[3]], limit=1)
            if partner:
                order_datra = {
                    # Transaction ID
                    'partner_id': partner and partner.id,  # Accounting ID
                    'client_order_ref': row[4],  # Purchase Order Number
                    'date_order': row[5],  # PO Date
                    'x_studio_full_delivery_address': ','.join(row[5:11]),
                    # Ship To Name # Ship To Address - Line One # Ship To Address - Line Two # Ship To City # Ship To State # Ship To Zip code # Ship To Country
                    # Store #
                    'x_studio_full_invoice_address': ','.join(row[13:20]),
                    # Bill To Name, Bill To Address - Line One, Bill To Address - Line Two, Bill To City, Bill To State, Bill To Zip code, Bill To Country, Bill To Code
                    'x_studio_ship_by': row[21],  # Ship Via
                    'commitment_date': row[22],  # Ship Dates
                    # Terms
                    'x_studio_order_note': row[24],  # Note
                    # Department Number
                    'x_studio_cancel_date': row[26],  # Cancel Date
                    # Do Not Ship Before
                    # Do Not Ship After
                    # Allowance Percent1
                    # Allowance Amount1
                    # Allowance Percent2
                    # Allowance Amount2
                }
                order = order.create({order_datra})
            else:
                print ('Partner not found---------------------', row[3])
        return order

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
        files = conn.ls()
        order = self.env['sale.order']
        order_line = self.env['sale.order.line']
        for file in files:
            file_path = os.path.join(sync_action_id.dir_path, file)
            file_data = conn.download_incoming_file(file_path).encode('utf-8')
        # with open('/home/prashant/Desktop/PurchaseOrder_20191209101823518.csv', '+r') as file_data:
            csv_reader = csv.reader(file_data, delimiter=',')
            line_count = 0
            rows = []
            for row in csv_reader:
                print ('rowww---------------------', row)
                if line_count == 0:
                    print(row)
                    try:
                        order = self.prepared_order_from_flatfile(row)
                        line_count = 1
                    except Exception as e:
                        _logger(e)
                        raise Warning(e)
                else:
                    rows.append(row)
            if order:
                try:
                    order_line = order_line.create(self.prepared_order_line_from_flatfile(order, rows))
                    print ('order---------------------', order)
                    print ('rows---------------------', rows)
                    print ('order_line---------------------', order_line)
                except Exception as e:
                    _logger(e)
                    raise Warning(e)
            else:
                print ('order not found---------------------', order)
        return True
