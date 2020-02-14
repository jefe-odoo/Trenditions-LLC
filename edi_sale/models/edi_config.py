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
            name = str(row[5])
            if not product:
                name = 'Product Not found FROM the EDI:\n Name: %s \n Barcode: %s \n Internal Ref: %s' % (row[5], row[2], row[3])
                product = self.env.ref('edi_sale.edi_product_product_error', raise_if_not_found=False)
                _logger.info('Product Not found FROM the EDI:\n Name: %s \n Barcode: %s \n Internal Ref: %s' % (row[5], row[2], row[3]))
            line_data = {
                'order_id': order.id,
                'product_id': product.id,
                'name': name,
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

    def create_partner(self, name=False, ref=False, address=[], type='contact', company_type='person', parent_id=False):
        res_partner = self.env['res.partner']
        if ref:
            res_partner = res_partner.search(['|', ('ref', 'ilike', ref), ('ref', '=', ref)], limit=1)
        elif name:
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
        if not res_partner:
            res_partner = self.env.ref('edi_sale.res_partner_error', raise_if_not_found=False)
            res_partner.message_post(body=_('EDI Partner Data not found, \n Name: %s \n REF: %s \n Address: %s' % (name, ref, address)))
        return res_partner

    def prepared_order_from_flatfile(self, row):
        # CAV090 is example where it is not dropship
        # CAV090 - customer reference.
        # CAV090 is ref field set on contact Cavenders Boot City #090
        # Parent is Cavenders
        # SO
        # -----
        # Customer = Cavenders Boot City# 090
        # Delivery address = Cavenders Boot City #090
        # Invoice address = Cavenders

        # TRA9999 is dropship
        # TRA9999 is ref field set on contact Tractor Supply Drop Ship Store
        # Parent is Tractor Supply
        # SO
        # -----
        # Customer = Tractor Supply Drop Ship Store
        # Delivery Address =(example) Hannah Wood
        # <With address details from flat file>
        # Invoice address = Tractor Supply
        partner = self.create_partner(ref=row[2], company_type='company')
        parent_id = partner.parent_id
        partner_id = partner
        partner_shipping_id = not partner.is_drop_ship and partner or self.create_partner(name=row[5], address=row[6:12], type='delivery')
        partner_invoice_id = parent_id or self.create_partner(name=row[13], address=row[14:20], type='invoice')
        payment_term = self.env['account.payment.term'].search([('name', 'ilike', row[23])], limit=1)
        order_data = {
            'name': self.env['ir.sequence'].next_by_code('edi.sale.order'),
            'partner_id': partner_id.id,
            'user_id': partner_id.user_id.id,
            'client_order_ref': row[3] or False,
            'date_order': row[4] and datetime.strptime(row[4], EDI_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT),  # PO Date
            'partner_shipping_id': partner_shipping_id.id,
            'partner_invoice_id': partner_invoice_id.id,
            'tra_store': row[12],
            'x_studio_ship_by': row[21] or False,
            'commitment_date': row[22] and datetime.strptime(row[22], EDI_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT) or False,  # Ship Dates
            'payment_term_id': payment_term and payment_term.id,
            'x_studio_order_notes': row[24] or False,
            'note': row[24] or False,
            'x_studio_cancel_date': row[26] and datetime.strptime(row[26], EDI_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT) or False,  # Cancel Date
            'is_edi_order': True,
        }
        # Do Not Ship Before
        # Do Not Ship After
        # Allowance Percent1
        # Allowance Amount1
        # Allowance Percent2
        # Allowance Amount2
        return order_data

    def _log_logging(self, name, message, function_name, path):
        return self.env['ir.logging'].sudo().create({
            'name': name,
            'type': 'server',
            'level': 'DEBUG',
            'dbname': self.env.cr.dbname,
            'message': message,
            'func': function_name,
            'path': path,
            'line': '0',
        })

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
            if not file.endswith('.csv'):
                continue
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
                    try:
                        if line_count == 0:
                            sale_order = order.search([('client_order_ref', '=', row[3]), ('tra_store', '=', row[12]), ('client_order_ref', '!=', False), ('tra_store', '!=', False)])
                            if sale_order:
                                _logger.warning('order already created from the file of %s and customer po: %s and store number: %s' % (file, row[3], row[12]))
                                break
                            order = order.create(self.prepared_order_from_flatfile(row))
                            _logger.info('Order Created: %s' % order.name)
                            line_count = 1
                        else:
                            rows.append(row)
                    except Exception as e:
                        lname = 'Order has required fields not set - FILE'
                        lmessage = str(e)
                        lfunc = '_do_import_so_flat'
                        lpath = file
                        self._log_logging(lname, lmessage, lfunc, lpath)
                        _logger.info('Order has required fields not set - FILE: %s ' % file)
                if order:
                    try:
                        order_line_data = self.prepared_order_line_from_flatfile(order, rows)
                        order_line = order_line.create(order_line_data)
                        # git the errro after create the order
                        # odoo.exceptions.CacheMiss:
                        self.flush()
                        order.sudo().message_post(body=_('Sale Order Created from the EDI File of: %s' % file))
                    except Exception as e:
                        lname = 'Order Line has required fields not set'
                        lmessage = str(e)
                        lfunc = '_do_import_so_flat'
                        lpath = str(file)
                        self._log_logging(lname, lmessage, lfunc, lpath)
                        _logger.info('Order Line has required fields not set - FILE: %s ' % file)
                file_data.close()
        conn._disconnect()
        return True
