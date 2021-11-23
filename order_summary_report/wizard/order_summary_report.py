# ======================================================
#     @Author: KSOLVES India Private Limited
#     @Email: sales@ksolves.com
# ======================================================

from odoo import api, fields, models
from datetime import date

class TrenditionOrderWarehouseReport(models.Model):
    _name = "trendition.order.summary.report"
    _description = "Order Summary Report"

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    name = fields.Char('Report Name', default="Order Summary Report", required=True)
    date_from = fields.Date('From')
    date_to = fields.Date('To')
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id, required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', default=_default_warehouse_id,
                                   readonly=True, required=True)

    customer_reference = fields.Char('Customer Reference')
    category_ids = fields.Many2many('product.category', 'rel_report_categ', 'report_id', 'categ_id',
                                    string="Categories")
    product_ids = fields.Many2many('product.product', 'rel_report_product', 'report_id', 'product_id',
                                   string="Products")
    customer_ids = fields.Many2many('res.partner', 'rel_report_customer', 'report_id', 'partner_id', string="Customers")

    # function: to get all data
    def get_lines(self):
        lines = []
        partner_list = []
        if self.customer_ids:
            for l in self.customer_ids:
                partner_list.append(l.id)
            partner_ids = self.env['res.partner'].search([('parent_id', 'in', self.customer_ids.ids),
                                                          ('type', 'in', ('invoice', 'delivery'))])
            if partner_ids:
                for p in partner_ids:
                    partner_list.append(p.id)
        warehouse = self.warehouse_id.id
        # if self.product_ids:
        #     product = self.env['product.product'].browse(self.product_ids.ids)
        # else:
        #     product = self.env['product.product'].search([])
        cr = self.env.cr
        cr.execute(
        "Select id "\
        "FROM product_product ")
        product_data = cr.fetchall()

        # if self.category_ids:
        #     stock_history = self.env['product.product'].search([('categ_id', 'in', self.category_ids.ids),
        #                                                         ('id', 'in', product.ids),
        #                                                         ('order_id.date_order', '>=', self.date_from),
        #                                                         ('order_id.date_order', '<=', self.date_to)])
        # else:
        #stock_history = self.env['product.product'].search([('id', 'in', product.ids)])
        for obj in product_data:
            current_stock = current_stock_value = 0
            sale_value = sale_amount = 0
            purchase_value = 0
            product = self.env['product.product'].browse(obj[0])
            if self.customer_ids and self.customer_reference:
                # sale_obj = self.env['sale.order.line'].search([('order_id.state', '!=', 'cancel'),
                #                                                ('product_id', '=', product.id),
                #                                                ('order_id.partner_id', 'in', partner_list),
                #                                                ('order_id.client_order_ref', 'ilike',
                #                                                 self.customer_reference),
                #                                                ])
                cr = self.env.cr
                cr.execute(
                "Select id, product_uom_qty, price_subtotal "\
                "FROM sale_order_line "\
                "WHERE "\
                "order_id in (select id from sale_order where state <> 'cancel' and partner_id in %s and client_order_ref ILIKE %s and create_date >= %s and create_date <= %s) and "\
                "product_id = %s", (tuple(partner_list), self.customer_reference +'%', self.date_from, self.date_to, product.id))
                sale_obj = cr.fetchall()
            else:
                # sale_obj = self.env['sale.order.line'].search([('order_id.state', '!=', 'cancel'),
                #                                                ('product_id', '=', product.id)
                #                                                ])


                cr = self.env.cr
                cr.execute(
                "Select id, product_uom_qty, price_subtotal "\
                "FROM sale_order_line "\
                "WHERE "\
                "order_id in (select id from sale_order where state <> 'cancel' and create_date >= %s and create_date <= %s) and "\
                "product_id = %s", (self.date_from,self.date_to, product.id))
                sale_obj = cr.fetchall()

            if sale_obj:
                for i in sale_obj:
                    sale_value = sale_value + i[1]
                    sale_amount = sale_amount + i[2]

                # purchase_obj = self.env['purchase.order.line'].search([('order_id.state', '=', 'draft'),
                #                                                        ('product_id', '=', product.id)
                #                                                        ])
                
                # for i in purchase_obj:
                #     purchase_value = purchase_value + i.product_qty
        
                cr = self.env.cr
                cr.execute(
                "Select id , product_qty "\
                "FROM purchase_order_line "\
                "WHERE "\
                "order_id in (select id from purchase_order where state = 'draft') and "\
                "product_id = %s" % (product.id))
                purchase_records = cr.fetchall()
                for i in purchase_records:
                    purchase_value = purchase_value + i[1]  

                #for on hand qty
                # quant_ids = self.env['stock.quant'].search([('company_id', '=', self.company_id.id),
                #                                             ('product_id', '=', product.id),
                #                                             ('location_id.usage', '=', 'internal')])
                # if quant_ids:
                #     current_stock += sum(l.quantity for l in quant_ids)                   
                # current_stock_value = current_stock * product.standard_price

                cr = self.env.cr
                cr.execute(
                "Select id , inventory_quantity "\
                "FROM stock_quant "\
                "WHERE "\
                "company_id = %s and "\
                "product_id = %s "\
                "and location_id in (select id from stock_location where usage = 'internal')", (self.company_id.id,product.id))
                quant_records = cr.fetchall()
                if quant_records:
                    current_stock += sum(l[1] for l in quant_records)                   
                current_stock_value = current_stock * product.standard_price

                #New code for changing On Hand Qty column to Qty Available column
                cr = self.env.cr
                cr.execute(
                "Select weight "\
                "FROM stock_move "\
                "WHERE "\
                "product_id in (select id from product_product where default_code = %(product)s)", {'product': product.default_code,})
                qty_available_list = cr.fetchall()
                qty_available = 0
                if qty_available_list:
                    qty_available += sum(l[0] for l in qty_available_list)
                #   qty_available = current_stock - qty_available


                #"default_code = %(product)s", {'product': product.default_code,})

                #New code for new column Expected PO Delivery Date
                cr = self.env.cr
                cr.execute(
                "Select x_studio_expected_arrival_date "\
                "FROM purchase_order "\
                "WHERE "\
                "partner_id in (select partner_id from purchase_order_line where product_id in (select id from product_product where default_code LIKE %s)) "\
                "and id in (select order_id from purchase_order_line where product_id in (select id from product_product where default_code LIKE %s)) "\
                "and x_studio_expected_arrival_date IS NOT NULL "\
                "and (state = 'draft' or state = 'sent')", (product.default_code, product.default_code))
                #SQL statement selects arrival dates based on default codes of items in purchase order. A combination of inner select statements gives the expected arrival dates of each item shown in any arbitray order summary report. Item's purchase order must have status RFQ or RFQ sent though.
                expected_delivery_dates = cr.fetchall()
                #The if statement and for loop in the next few lines pick the closest date of delivery for the items in the order summary reports and assigns that value to expected_delivery_date, passing it into the order_summary_report.xml file.                
                if expected_delivery_dates:
                    expected_delivery_date = expected_delivery_dates[0][0]
                    for i in expected_delivery_dates:
                        if i[0] < expected_delivery_date:
                            expected_delivery_date = i[0]
                else:
                    expected_delivery_date = expected_delivery_dates
                    
                vals = {
                    'sku': product.default_code,
                    'name': product.name,
                    'category': product.categ_id.name,
                    'available': product.qty_available,
                    'sale_value': round(sale_value, 2),
                    'sale_amount': round(sale_amount, 2),
                    'purchase_value': purchase_value,
                    #'current_stock': current_stock,
                    'current_stock_value': current_stock_value,
                    'x_studio_bin_location_v': product.x_studio_bin_location_v,
                    'expected_delivery_date': expected_delivery_date,
                    'qty_available': current_stock,
                }
                lines.append(vals)
        return lines

    def generate_pdf_report(self):
        return self.env.ref('order_summary_report.report_order_summary').report_action(self)
