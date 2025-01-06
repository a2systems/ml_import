# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    pos_other_company_id = fields.Many2one('res.company','POS Otra Empresa')
    pos_other_journal_id = fields.Many2one('account.journal',string='POS Otro Medio de Pago')
