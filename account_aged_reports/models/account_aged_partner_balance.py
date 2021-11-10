# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date

class report_account_aged_partner(models.AbstractModel):
    _inherit = "account.aged.partner"

    def _get_columns_name(self, options):
        columns = super()._get_columns_name(options)
        # custom code begins:- added 'Paymnet Terms' columns in reports
        columns.insert(2,{'name': ("Payment Terms"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'})
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        context = {'include_nullified_amount': True}
        if line_id and 'partner_' in line_id:
            # we only want to fetch data about this partner because we are expanding a line
            partner_id_str = line_id.split('_')[1]
            if partner_id_str.isnumeric():
                partner_id = self.env['res.partner'].browse(int(partner_id_str))
            else:
                partner_id = False
            context.update(partner_ids=partner_id)
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(**context)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)

        for values in results:
            # custom code begins:- just improve 5 in 'columns' instead of 4 because we added one more column
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 5 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                 for v in [values['direction'], values['4'],
                                                           values['3'], values['2'],
                                                           values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                'partner_id': values['partner_id'],
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name,
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [format_date(self.env, aml.date_maturity or aml.date), aml.move_id.invoice_payment_term_id.name, aml.journal_id.code, aml.account_id.display_name, format_date(self.env, aml.expected_pay_date)]] +
                                   [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 6-i and line['amount'] or 0 for i in range(7)]],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                    }
                    lines.append(vals)
        if total and not line_id:
            # custom code begins:- just improve 5 in 'columns' instead of 4 because we added one more column
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 5 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines

class ReportAccountAgedPartner(models.AbstractModel):
    _name = "account.aged.partner.date"
    _inherit = 'account.aged.partner'

    def _get_columns_name(self, options):
        columns = super()._get_columns_name(options)
        ctx = self._context
        if ctx.get('account_type') == 'payable' and ctx.get('model') == 'account.aged.payable.date':
            columns.insert(1,{'name': _('Bill Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'})
        if ctx.get('account_type') == 'receivable' and ctx.get('model') == 'account.aged.receivable.date':
            columns.insert(1,{'name': _('Invoice Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'})
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        context = {'include_nullified_amount': True}
        if line_id and 'partner_' in line_id:
            # we only want to fetch data about this partner because we are expanding a line
            partner_id_str = line_id.split('_')[1]
            if partner_id_str.isnumeric():
                partner_id = self.env['res.partner'].browse(int(partner_id_str))
            else:
                partner_id = False
            context.update(partner_ids=partner_id)
            # custom code begins:- use new report model and it's method
        results, total, amls = self.env['report.account.report_agedpartnerbalance_custom'].with_context(**context)._get_partner_move_lines_custom(account_types, self._context['date_to'], 'posted', 30)

        for values in results:
            # custom code begins:- just improve 6 in 'columns' instead of 4 because we added two more columns in 'receivable' and 'payable'
            if self.env.context.get('model') == 'account.aged.receivable.date' or self.env.context.get('model') == 'account.aged.payable.date':
                vals = {
                    'id': 'partner_%s' % (values['partner_id'],),
                    'name': values['name'],
                    'level': 2,
                    'columns': [{'name': ''}] * 6 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                     for v in [values['direction'], values['4'],
                                                               values['3'], values['2'],
                                                               values['1'], values['0'], values['total']]],
                    'trust': values['trust'],
                    'unfoldable': True,
                    'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                    'partner_id': values['partner_id'],
                }
            # custom code begins:- just improve 5 in 'columns' instead of 4 because we added one more columns in 'receivable' and 'payable'
            else:
                vals = {
                    'id': 'partner_%s' % (values['partner_id'],),
                    'name': values['name'],
                    'level': 2,
                    'columns': [{'name': ''}] * 5 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                     for v in [values['direction'], values['4'],
                                                               values['3'], values['2'],
                                                               values['1'], values['0'], values['total']]],
                    'trust': values['trust'],
                    'unfoldable': True,
                    'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                    'partner_id': values['partner_id'],
                }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    if self.env.context.get('model') == 'account.aged.receivable.date' or self.env.context.get('model') == 'account.aged.payable.date':
                        vals = {
                            'id': aml.id,
                            'name': aml.move_id.name,
                            'class': 'date',
                            'caret_options': caret_type,
                            'level': 4,
                            'parent_id': 'partner_%s' % (values['partner_id'],),
                            'columns': [{'name': v} for v in [format_date(self.env, aml.move_id.invoice_date),format_date(self.env, aml.date_maturity or aml.date), aml.move_id.invoice_payment_term_id.name, aml.journal_id.code, aml.account_id.display_name, format_date(self.env, aml.expected_pay_date)]] +
                                       [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 6-i and line['amount'] or 0 for i in range(7)]],
                            'action_context': {
                                'default_type': aml.move_id.type,
                                'default_journal_id': aml.move_id.journal_id.id,
                            },
                            'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                        }
                    else:
                        vals = {
                            'id': aml.id,
                            'name': aml.move_id.name,
                            'class': 'date',
                            'caret_options': caret_type,
                            'level': 4,
                            'parent_id': 'partner_%s' % (values['partner_id'],),
                            'columns': [{'name': v} for v in [format_date(self.env, aml.date_maturity or aml.date), aml.move_id.invoice_payment_term_id.name, aml.journal_id.code, aml.account_id.display_name, format_date(self.env, aml.expected_pay_date)]] +
                                       [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 6-i and line['amount'] or 0 for i in range(7)]],
                            'action_context': {
                                'default_type': aml.move_id.type,
                                'default_journal_id': aml.move_id.journal_id.id,
                            },
                            'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                        }
                    lines.append(vals)
        if total and not line_id:
            # custom code begins:- just improve 6 in 'columns' instead of 4 because we added two more column
            if self.env.context.get('model') == 'account.aged.receivable.date' or self.env.context.get('model') == 'account.aged.payable.date':
                total_line = {
                    'id': 0,
                    'name': _('Total'),
                    'class': 'total',
                    'level': 2,
                    'columns': [{'name': ''}] * 6 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
                }
            # custom code begins:- just improve 5 in 'columns' instead of 4 because we added one more column
            else:
                total_line = {
                    'id': 0,
                    'name': _('Total'),
                    'class': 'total',
                    'level': 2,
                    'columns': [{'name': ''}] * 5 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
                }
            lines.append(total_line)
        return lines

# create new custom 'Aged Receivable Report By Invoice Date'
class ReportAccountAgedReceivable(models.AbstractModel):
    _name = "account.aged.receivable.date"
    _description = "Aged Receivable By Invoice Date"
    _inherit = "account.aged.partner.date"

    def _set_context(self, options):
        ctx = super(ReportAccountAgedReceivable, self)._set_context(options)
        ctx['account_type'] = 'receivable'
        return ctx

    def _get_report_name(self):
        return _("Aged Receivable By Invoice Date")

    def _get_templates(self):
        templates = super(ReportAccountAgedReceivable, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_aged_receivable_report'
        return templates

# create new custom 'Aged Payable Report By Bill Date'
class ReportAccountAgedPayable(models.AbstractModel):
    _name = "account.aged.payable.date"
    _description = "Aged Payable  By Bill Date"
    _inherit = "account.aged.partner.date"

    def _set_context(self, options):
        ctx = super(ReportAccountAgedPayable, self)._set_context(options)
        ctx['account_type'] = 'payable'
        ctx['aged_balance'] = True
        return ctx

    def _get_report_name(self):
        return _("Aged Payable By Bill Date")

    def _get_templates(self):
        templates = super(ReportAccountAgedPayable, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_aged_payable_report'
        return templates
