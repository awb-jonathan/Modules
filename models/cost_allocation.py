from odoo import api, fields, models, _
from datetime import datetime, date
import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

COST_ALLOC_APPLICATION = [
    ('internet', 'Internet'),
    ('program_cost', 'Program Cost'),
    ('salaries', 'Salaries'),
    ('others', 'Others')]
COST_ALLOC_STATUS = [
    ('draft', 'Draft'),
    ('allocated', 'Allocated'),
    ('posted', 'Posted')]
LINE_TYPE = [
    ('debit', 'Debit'),
    ('credit', 'Credit'),]


class CostAllocationLine(models.Model):
    _name = "cost.allocation.line"
    _description = "Cost Allocation Line"

    cost_allocation_id = fields.Many2one('cost.allocation', string="Cost Allocation ID")
    date = fields.Date(string="Date", default=datetime.today())
    account_id = fields.Many2one('account.account', string="Account",
        index=True, ondelete="restrict", check_company=True,
        domain=[('deprecated', '=', False)])
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='restrict')
    name = fields.Char(string="Label")
    debit = fields.Float(string="Debit", default=0.0, digits=dp.get_precision("COST ALLOCATION PRECISION"))
    credit = fields.Float(string="Credit", default=0.0, digits=dp.get_precision("COST ALLOCATION PRECISION"))
    values = fields.Float(string="Values")
    share = fields.Float(string="Share")
    line_type = fields.Selection(LINE_TYPE, string="Type")
    tax_ids = fields.Many2many('account.tax', string="Taxes", help="Taxes that apply on the base amount")
    tag_ids = fields.Many2many(string="Tags", comodel_name='account.account.tag', ondelete='restrict',
        help="Tags assigned to this line by the tax creating it, if any. It determines its impact on financial reports.")


class CostAllocation(models.Model):
    _name = "cost.allocation"
    _description = "Cost Allocation"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", index=True, default=lambda self: _('New'), readonly=True,)
    description = fields.Text(string="Description")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    accounting_date = fields.Date(string="Accounting Date", required=True)
    debit_account_id = fields.Many2one('account.account', string="Debit Account", required=True)
    debit_analytic_account_id = fields.Many2many(
        'account.analytic.account',
        'account_analytic_debit',
        'account_analytic_id',
        'debit_analytic_account_id',
        string="Debit Analytic Account")
    credit_account_id = fields.Many2one('account.account', string="Credit Account", required=True)
    credit_other_analytic_account_id = fields.Many2many(
        'account.analytic.account',
        'account_analytic_credit',
        'account_analytic_id',
        'credit_analytic_account_id',
        string="Credit Analytic Account")
    credit_analytic_account_id = fields.Many2one('account.analytic.account', string="Credit Analytic Account")
    journal_id = fields.Many2one('account.journal', string="Journal", required=True)
    posted_date = fields.Date(string="Posted Date")
    factor = fields.Float(string="Factor", required=True)
    basis = fields.Float(string="Basis", required=True)
    application = fields.Selection(COST_ALLOC_APPLICATION, string="Application", default='internet')
    state = fields.Selection(COST_ALLOC_STATUS, string="Status", default='draft')
    cost_allocation_line = fields.One2many('cost.allocation.line', 'cost_allocation_id', string="Journal Items")

    # button
    # Compute
    def button_compute_source_information(self):
        sale_subscription_obj = self.env['sale.subscription']
        start_date = self.start_date
        end_date = self.end_date
        debit_account_id = self.debit_account_id.id
        credit_account_id = self.credit_account_id.id
        application = self.application
        self.update({"cost_allocation_line": None})
        if application == 'internet':
            _logger.debug(f'COMPUTE INTERNET')
            journal_item = []
            debit_line_dict = {}
            credit_line_dict = {}
            debit_analytic_ids = [rec.id for rec in self.debit_analytic_account_id]
            # Debit
            debit_args = [
                        ("partner_id.subscriber_location_id.analytic_account_id", "in", debit_analytic_ids),
                        ("date_start", ">=", start_date),
                        ("date_start", "<=", end_date),
                        ("stage_id.name", "not in", ["Draft", "Closed"])]
            debit_subscription = sale_subscription_obj.search(debit_args)
            credit_value = 0
            for rec_list in debit_subscription:
                debit_subscriber_id = rec_list.partner_id.subscriber_location_id
                if debit_subscriber_id.id not in debit_line_dict:
                    debit_line_dict[debit_subscriber_id.id] = {
                        "date": self.accounting_date,
                        "account_id": debit_account_id,
                        "analytic_account_id": debit_subscriber_id.analytic_account_id.id,
                        "partner_id": None,
                        "name": self.name,
                        "debit": 0.00,
                        "credit": 0.00,
                        "values": 0.00,
                        "share": 0.00,
                        "cost_allocation_id": self.id,
                        "line_type": 'debit',
                        }
                for rec in rec_list.recurring_invoice_line_ids:
                    debit_line_dict[debit_subscriber_id.id]['values'] += rec.product_id.internet_usage
                    credit_value += rec.product_id.internet_usage
            for key, item in debit_line_dict.items():
                journal_item.append((0, 0, item))
            # Credit
            credit_analytic_ids = self.credit_analytic_account_id.id
            credit_line_dict = {
                "date": self.accounting_date,
                "account_id": credit_account_id,
                "analytic_account_id": credit_analytic_ids,
                "partner_id": None,
                "name": self.name,
                "debit": 0.00,
                "credit": 0.00,
                "values": credit_value,
                "share": 0.00,
                "cost_allocation_id": self.id,
                "line_type": 'credit',
                }
            journal_item.append((0, 0, credit_line_dict))
            self.update({"cost_allocation_line": journal_item, "state": "draft", "factor": credit_value})

        elif application == 'program_cost':
            return True
        elif application == 'salaries':
            return True
        elif application == 'others':
            _logger.debug(f'Others')
            # Do nothing
    # Allocate
    def button_allocate_amount_and_share(self):
        factor = self.factor
        basis = self.basis
        share = 0
        amount = 0
        for record in self.cost_allocation_line:
            share = record.values / factor
            amount = basis * share
            if record.line_type == 'debit':
                record.write({"share": share, "debit": amount})
            elif record.line_type == 'credit':
                record.write({"share": share, "credit": amount})
        self.write({"state": "allocated"})
        return True
    # Post
    def button_posting_journal_entries(self):
        # Create Journal Entry
        data = []
        for record in self.cost_allocation_line:
            raw_data = {
                        'account_id': record.account_id.id,
                        'name': record.name,
                        'analytic_account_id': record.analytic_account_id.id,
                        'debit': record.debit,
                        'credit': record.credit}
            data.append((0, 0, raw_data))

        journal_entry = self.env['account.move'].create({
            'ref': self.name,
            'date': self.accounting_date,
            'journal_id': self.journal_id.id,
            'line_ids': data,
            })
        # call posting of journat entry
        journal_entry.post()
        self.write({"state": "posted", "posted_date": date.today()})
        return True

    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('cost.allocation.seq.code')
        res = super(CostAllocation, self).create(vals)
        return res