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
    debit_analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        'account_analytic_debit',
        'account_analytic_id',
        'debit_analytic_account_id',
        string="Debit Analytic Account")
    credit_account_id = fields.Many2one('account.account', string="Credit Account", required=True)
    credit_analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        'account_analytic_credit',
        'account_analytic_id',
        'credit_analytic_account_id',
        string="Credit Analytic Account")
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
        location_obj = self.env['subscriber.location']
        sale_subscription_obj = self.env['sale.subscription']
        sale_subscription_line_obj = self.env['sale.subscription.line']
        start_date = self.start_date
        end_date = self.end_date
        debit_account_id = self.debit_account_id.id
        application = self.application
        self.update({"cost_allocation_line": None})
        item_code = ['debit', 'credit']
        if application == 'internet':
            _logger.debug(f'Compute Internet')
            credit_internet_usage = 0
            journal_item = []
            cost_allocation_line_dict = {}
            # Search in Location based on the Debit Analytic Accounts.
            debit_analytic_ids = [rec.id for rec in self.debit_analytic_account_ids]
            # Debit
            subscription_args = [
                                ("partner_id.subscriber_location_id.analytic_account_id", "in", debit_analytic_ids),
                                ("date_start", '>=', start_date),
                                ("date_start", '<=', end_date),
                                ("stage_id.name", "not in", ["Draft","Closed"])]
            subscription_list = sale_subscription_obj.search(subscription_args)
            _logger.debug(f'subscription_list: {subscription_list}')
            for rec_list in subscription_list:
                debit_internet_usage = 0
                subscriber_location_id = rec_list.partner_id.subscriber_location_id
                cost_allocation_line = {
                    "date": self.accounting_date,
                    "account_id": debit_account_id,
                    "analytic_account_id": subscriber_location_id.analytic_account_id.id,
                    "partner_id": None,
                    "name": self.name,
                    "debit": 0.00,
                    "credit": 0.00,
                    "values": 0.00,
                    "share": 0.00,
                    "cost_allocation_id": self.id,
                    }
                cost_allocation_line_dict[subscriber_location_id.id] = cost_allocation_line
                for rec in rec_list.recurring_invoice_line_ids:
                    debit_internet_usage += rec.product_id.internet_usage
                    _logger.debug(f'debit_internet_usage: {debit_internet_usage} || subscriber_location_id: {subscriber_location_id.id}')
                    cost_allocation_line['debit'] = debit_internet_usage

                _logger.debug(f'cost_allocation_line_dict: {cost_allocation_line_dict}')
            for key, item in cost_allocation_line_dict.items():
                journal_item.append((0, 0, item))
            # journal_item.append((0, 0, cost_allocation_line))
            self.update({"cost_allocation_line": journal_item})

        elif application == 'program_cost':
            return True
        elif application == 'salaries':
            return True
        elif application == 'others':
            return True

    # Allocate
    def button_allocate_amount_and_share(self):
        return True
    # Post
    def button_posting_journal_entries(self):
        return True

    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('cost.allocation.seq.code')
        res = super(CostAllocation, self).create(vals)
        return res