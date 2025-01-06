# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"


    @api.model
    def create_order_from_pos(self, order_data, action):
        # Create Draft Sale order
        order_vals = self._prepare_from_pos(order_data)
        sale_order = self.with_context(
            pos_order_lines_data=[x[2] for x in order_data.get("lines", [])]
        ).create(order_vals)

        # Confirm Sale Order
        if action in ["confirmed", "delivered", "invoiced"]:
            sale_order.action_confirm()

        # mark picking as delivered
        if action in ["delivered", "invoiced"]:
            # Mark all moves are delivered
            for move in sale_order.mapped("picking_ids.move_ids_without_package"):
                move.quantity = move.product_uom_qty
            sale_order.mapped("picking_ids").button_validate()

        if action in ["invoiced"]:
            # Create and confirm invoices
            pos_session_id = order_data.get('pos_session_id',0)
            new_co_id = None
            new_journal_id = None
            if pos_session_id:
                session_id = self.env['pos.session'].browse(pos_session_id)
                config_id = session_id.config_id
                new_co_id = config_id.pos_other_company_id
                new_journal_id = config_id.pos_other_journal_id
            if not new_co_id:
                invoices = sale_order._create_invoices()
                invoices.sudo().action_post()
            else:
                invoices = sale_order.sudo().with_context(other_company=new_co_id.id,new_journal_id=new_journal_id.id)._create_invoices()
                invoices.sudo().action_post()
                for inv in invoices:
                    vals_payment = {
                        'partner_id': inv.partner_id.id,
                        'journal_id': new_journal_id.id,
                        'date': inv.invoice_date,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'amount': inv.amount_total,
                        'ref': inv.display_name,
                        'company_id': new_co_id.id,
                        }
                    payment_id = self.env['account.payment'].create(vals_payment)
                    payment_id.action_post()
                    aml_obj = self.env['account.move.line']
                    for move_line in inv.sudo().line_ids:
                        if move_line.account_id.account_type == 'asset_receivable':
                            aml_obj += move_line
                    for move_line in payment_id.line_ids:
                        if move_line.account_id.account_type == 'asset_receivable':
                            aml_obj += move_line
                    #aml_obj.sudo().reconcile()
        return {
            "sale_order_id": sale_order.id,
        }

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.env.context.get('other_company'):
            res['company_id'] = self.env.context.get('other_company')
        return res

    newco_inv_id = fields.Many2one('account.move',string='NewCo Invoice')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        if self.env.context.get('other_company'):
            new_external_id = 'account.%s_ri_tax_vat_21_ventas'%(self.env.context.get('other_company'))
            new_tax = self.env.ref(new_external_id).id
            res['tax_ids'] = [(6,0,[new_tax])]
        return res

"""
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [Command.set(self.tax_id.ids)],
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
        }
        self._set_analytic_distribution(res, **optional_values)
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res


    def _prepare_invoice(self):
        self.ensure_one()

        values = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(self.partner_invoice_id)).id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_user_id': self.user_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [Command.set(self.transaction_ids.ids)],
            'company_id': self.company_id.id,
            'invoice_line_ids': [],
            'user_id': self.user_id.id,
        }
        if self.journal_id:
            values['journal_id'] = self.journal_id.id
        return values
"""
