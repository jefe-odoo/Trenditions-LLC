# ======================================================
#     @Author: KSOLVES India Private Limited
#     @Email: sales@ksolves.com
# ======================================================

from odoo import api, fields, models


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
        if self.product_ids:
            product = self.env['product.product'].browse(self.product_ids.ids)
        else:
            product = self.env['product.product'].search([])
        # if self.category_ids:
        #     stock_history = self.env['product.product'].search([('categ_id', 'in', self.category_ids.ids),
        #                                                         ('id', 'in', product.ids),
        #                                                         ('order_id.date_order', '>=', self.date_from),
        #                                                         ('order_id.date_order', '<=', self.date_to)])
        # else:
        stock_history = self.env['product.product'].search([('id', 'in', product.ids)])
        for obj in stock_history:
            current_stock = current_stock_value = 0
            sale_value = sale_amount = 0
            purchase_value = 0
            product = self.env['product.product'].browse(obj.id)
            if self.customer_ids and self.customer_reference:
                sale_obj = self.env['sale.order.line'].search([('order_id.state', 'in', ('sale', 'done')),
                                                               ('product_id', '=', product.id),
                                                               ('order_id.partner_id', 'in', partner_list),
                                                               ('order_id.client_order_ref', 'ilike',
                                                                self.customer_reference),
                                                               ])
            else:
                sale_obj = self.env['sale.order.line'].search([('order_id.state', 'in', ('sale', 'done')),
                                                               ('product_id', '=', product.id)
                                                               ])

            if sale_obj:
                for i in sale_obj:
                    sale_value = sale_value + i.product_uom_qty
                    sale_amount = sale_amount + i.price_subtotal
                purchase_obj = self.env['purchase.order.line'].search([('order_id.state', '=', 'draft'),
                                                                       ('product_id', '=', product.id)
                                                                       ])
                for i in purchase_obj:
                    purchase_value = purchase_value + i.product_qty

                # for on hand qty
                quant_ids = self.env['stock.quant'].search([('company_id', '=', self.company_id.id),
                                                            ('product_id', '=', product.id),
                                                            ('location_id.usage', '=', 'internal')])
                if quant_ids:
                    current_stock += sum(l.quantity for l in quant_ids)
                current_stock_value = current_stock * product.standard_price
                vals = {
                    'sku': product.default_code,
                    'name': product.name,
                    'category': product.categ_id.name,
                    'available': product.qty_available,
                    'sale_value': round(sale_value, 2),
                    'sale_amount': round(sale_amount, 2),
                    'purchase_value': purchase_value,
                    'current_stock': current_stock,
                    'current_stock_value': current_stock_value,
                    'x_studio_bin_location_v': product.x_studio_bin_location_v,
                }
                lines.append(vals)
        return lines

    def generate_pdf_report(self):
        return self.env.ref('order_summary_report.report_order_summary').report_action(self)
