from odoo import api, fields, models, _


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

    @api.onchange('state')
    def _onchange_set_to_check(self):
        if self.user_has_groups('account.group_account_invoice'):
            self.to_check = True