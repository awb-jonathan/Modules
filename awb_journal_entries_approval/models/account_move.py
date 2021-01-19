from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Journal Entries"

    reviewed_by = fields.Many2one('res.users', string="Reviewed by")
    approved_by = fields.Many2one('res.users', string="Approved by")
    state = fields.Selection(selection_add=[('reviewed', 'Reviewed')])

    def action_review(self):
        current_user = self.env.user
        self.write({"state": "reviewed", "reviewed_by": current_user})

    def action_post(self):
        res = super(AccountMove, self).action_post()
        current_user = self.env.user
        self.write({"approved_by": current_user})
        return res

    @api.model
    def create(self, vals):
        vals['to_check'] = False
        if self.user_has_groups('account.group_account_invoice'):
            vals['to_check'] = True
        res = super(AccountMove, self).create(vals)
        return res