# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tra_store = fields.Char('Related Store #')
    is_edi_order = fields.Boolean("EDI Order")
