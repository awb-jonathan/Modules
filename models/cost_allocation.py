from odoo import api, fields, models, _
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
    date = fields.Date(string="Date")
    account_id = fields.Many2one('account.account', string="Account",
        index=True, ondelete="restrict", check_company=True,
        domain=[('deprecated', '=', False)])
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
    posted_date = fields.Date(string="Posted Date", required=True)
    factor = fields.Float(string="Factor", required=True)
    basis = fields.Float(string="Basis", required=True)
    application = fields.Selection(COST_ALLOC_APPLICATION, string="Application", default='internet')
    state = fields.Selection(COST_ALLOC_STATUS, string="Status")
    cost_allocation_line = fields.One2many('cost.allocation.line', 'cost_allocation_id', string="Journal Items")

    # button
    # Compute
    def button_compute_source_information(self):
        start_date = self.start_date
        end_date = self.end_date
        debit = self.debit_account_id
        debit_analytic = self.debit_analytic_account_ids


        

        credit = self.credit_account_id
        credit_analytic = self.credit_analytic_account_ids

        _logger.debug(f'start_date: {start_date} || end_date: {end_date}')
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