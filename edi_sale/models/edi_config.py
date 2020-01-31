# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
import pprint
import logging
import csv
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


from odoo import fields, models, _

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
        product_product = self.env['product.product']
        for row in rows:
            product = product_product.search(['|', ('barcode', 'in', [row[2], row[4]]), ('default_code', '=', row[3])], limit=1)
            uom = self.env['uom.uom'].search([('name', 'ilike', row[7])], limit=1)
            if not product:
                product = product_product.create({'name': row[5], 'barcode': row[2], 'default_code': row[3], 'uom_id': uom and uom.id})
            line_data = {
                'order_id': order.id,
                'product_id': product.id,
                'name': str(row[5]),
                'product_uom_qty': float(row[6]),
                'product_uom': uom and uom.id,
                'price_unit': float(row[8]),
                'display_type': False,
            }
            # Pack Size
            # # of Inner Packs
            # Item Allowance Percent1
            # Item Allowance Amount1
            order_line_data.append(line_data)
        return order_line_data

    def create_partner(self, name=False, address=[], type='contact', company_type='person', parent_id=False):
        res_partner = self.env['res.partner']
        res_partner = res_partner.search(['|', ('name', 'ilike', name), ('name', '=', name)], limit=1)
        if name and not res_partner:
            data = {
                    'name': name,
                    'type': type,
                    'company_type': company_type,
                    'parent_id': parent_id,
                }
            if address:
                state = self.env['res.country.state'].search([('code', '=', address[3])], limit=1)
                country = self.env['res.country'].search([('code', '=', address[5])], limit=1)
                data.update({
                    'street': address[0],
                    'street2': address[1],
                    'city': address[2],
                    'state_id': state and state.id,
                    'zip': address[4],
                    'country_id': country and country.id,
                    })
            res_partner = res_partner.create(data)
        return res_partner and res_partner.id

    def prepared_order_from_flatfile(self, row):
        partner_id = self.create_partner(row[2], [], company_type='company')
        partner_shipping_id = self.create_partner(row[5], row[6:12], 'delivery', parent_id=partner_id)
        partner_invoice_id = self.create_partner(row[13], row[14:20], 'invoice', parent_id=partner_id)
        payment_term = self.env['account.payment.term'].search([('name', 'ilike', row[23])], limit=1)
        order_data = {
            'partner_id': partner_id,
            'client_order_ref': row[3] or False,
            'date_order': row[4] and datetime.strptime(row[4], EDI_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT),  # PO Date
            'partner_shipping_id': partner_shipping_id,
            'partner_invoice_id': partner_invoice_id,
            'tra_store': row[12],
            'x_studio_ship_by': row[21] or False,
            'commitment_date': row[22] and datetime.strptime(row[22], EDI_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT) or False,  # Ship Dates
            'payment_term_id': payment_term and payment_term.id,
            'x_studio_order_notes': row[24] or False,
            'note': row[24] or False,
            'x_studio_cancel_date': row[26] and datetime.strptime(row[26], EDI_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT) or False,  # Cancel Date
        }
        # Do Not Ship Before
        # Do Not Ship After
        # Allowance Percent1
        # Allowance Amount1
        # Allowance Percent2
        # Allowance Amount2
        return order_data

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
        order = self.env['sale.order'].sudo()
        order_line = self.env['sale.order.line'].sudo()
        for file in files:
            file_path = os.path.join(sync_action_id.dir_path, file)
            temp_file = 'temp.csv'
            data = open(temp_file, 'wb')
            conn._conn.retrbinary('RETR %s' % file_path, data.write)
            data.close()
            with open(temp_file, 'rt') as file_data:
                csv_reader = csv.reader(file_data, delimiter=',')
                line_count = 0
                rows = []
                for row in csv_reader:
                    if line_count == 0:
                        try:
                            order = order.create(self.prepared_order_from_flatfile(row))
                            line_count = 1
                        except Exception:
                            _logger.error('Order has required fields not set - FILE: %s ' % file)
                    else:
                        rows.append(row)
                if order:
                    try:
                        order_line_data = self.prepared_order_line_from_flatfile(order, rows)
                        order_line = order_line.create(order_line_data)
                        # git the errro after create the order
                        # odoo.exceptions.CacheMiss:
                        self.flush()
                    except Exception:
                        _logger.error('Order Line has required fields not set - FILE: %s ' % file)
                file_data.close()
                if order:
                    order.sudo().message_post(body=_('Sale Order Created from the EDI File of: %s' % file))
        conn._disconnect()
        return True
