# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.move_type in ['out_invoice','out_refund'] and 'new_journal_id' in self.env.context:
                vals_payment = {
                        'partner_id': rec.partner_id.id,
                        'journal_id': self.env.context.get('new_journal_id'),
                        'date': rec.invoice_date,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'amount': rec.amount_total,
                        'ref': rec.display_name,
                        'company_id': self.env.context.get('other_company'),
                        }
                payment_id = self.env['account.payment'].create(vals_payment)
                payment_id.action_post()
                aml_obj = self.env['account.move.line']
                for move_line in rec.line_ids:
                    if move_line.account_id.account_type == 'asset_receivable':
                        aml_obj += move_line
                for move_line in payment_id.line_ids:
                    if move_line.account_id.account_type == 'asset_receivable':
                        aml_obj += move_line
                #aml_obj.sudo().reconcile()
        return res

