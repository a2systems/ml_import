# Copyright (C) 2017 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_other_company_id = fields.Many2one(
            'res.company',
            'POS Otra Empresa',
            related='pos_config_id.pos_other_company_id',
            readonly=False
            )
    pos_other_journal_id = fields.Many2one(
            'account.journal',
            string='POS Otro Medio de Pago',
            related='pos_config_id.pos_other_journal_id',
            readonly=False
            )
    
