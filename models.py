# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from unicodedata import name
from dateutil.relativedelta import relativedelta
from datetime import date,datetime,timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError

import base64
import csv
from io import StringIO
from io import BytesIO
import openpyxl

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ml_file_id = fields.Many2one('ml.file',string='Archivo ML')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ml_file_id = fields.Many2one('ml.file',string='Archivo ML')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    ml_file_id = fields.Many2one('ml.file',string='Archivo ML')

class MlFile(models.Model):
    _name = "ml.file"
    _inherit = ['mail.thread','mail.activity.mixin']  
    _description = "Importacion MercadoLibre"

    name = fields.Char('Nombre',tracking=True)
    date = fields.Date('Fecha Ingreso',default=fields.Date.today(),readonly=True)
    sales_file = fields.Binary('Archivo')
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("done", "Procesado"),
        ],
        default="draft",
        tracking=True
    )
    partner_ids = fields.One2many(comodel_name="res.partner", inverse_name="ml_file_id",string='Clientes creados',readonly=True)
    product_ids = fields.One2many(comodel_name="product.product", inverse_name="ml_file_id",string='Productos creados',readonly=True)
    sale_ids = fields.One2many(comodel_name="sale.order", inverse_name="ml_file_id",string='Pedidos creadas',readonly=True)

    def btn_process_file(self):
        self.ensure_one()
        if not self.sales_file:
            raise ValidationError('Por favor ingrese el archivo')
        if self.state != 'draft':
            raise ValidationError('Estado incorrecto')
        wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.sales_file)),read_only=True)
        # ordenes 
        worksheet = wb.worksheets[0]
        rows = worksheet.rows
        for x,row in enumerate(rows):
            # Saltea la primer fila porque tiene el nombre de las columnas
            if x == 0:
                continue
            # Lee cada una de las celdas en la fila
            vals = {}
            client_order_ref = None
            product_uom_qty = 0
            default_code = None
            description = None
            prod_name = None
            customer_name = None
            street = None
            resp_fiscal = None
            for i,cell in enumerate(row):
                if i == 0 and cell.value:
                    client_order_ref = cell.value
                if i == 1 and cell.value:
                    product_uom_qty = cell.value
                if i == 2 and cell.value:
                    default_code = str(cell.value)
                if i == 3 and cell.value:
                    description = str(cell.value)
                if i == 4 and cell.value:
                    prod_name = str(cell.value)
                if i == 5 and cell.value:
                    price_unit = cell.value / 1.21
                if i == 7 and cell.value:
                    customer_name = cell.value
                if i == 9 and cell.value:
                    street = cell.value
                if i == 8 and cell.value:
                    tipo_doc,num_doc = cell.value.split(' ')
                if i == 10 and cell.value:
                    resp_fiscal = cell.value
            if default_code:
                vals_prod = {
                        'default_code': default_code,
                        'type': 'product',
                        'name': prod_name,
                        'description': description,
                        }
                product_id = self.env['product.product'].search([('default_code','=',default_code)])
                if not product_id:
                    product_id = self.env['product.product'].create(vals_prod)
            if client_order_ref and tipo_doc and num_doc:
                partner_id = self.env['res.partner'].search([('vat','=',num_doc)])
                if not partner_id:
                    vals_partner = {
                        'ml_file_id': self.id,
                        'name': customer_name,
                        'street': street,
                        'customer_rank': 1,
                        }
                    if tipo_doc.startswith('DNI'):
                        vals_partner['l10n_latam_identification_type_id'] = 5
                    else:
                        vals_partner['l10n_latam_identification_type_id'] = 4
                    partner_id = self.env['res.partner'].create(vals_partner)
                    partner_id.write({'vat': num_doc})
                    if resp_fiscal:
                        if resp_fiscal.startswith('Consumidor'):
                            partner_id.write({'l10n_ar_afip_responsibility_type_id': 5})
                        elif resp_fiscal.startswith('IVA'):
                            partner_id.write({'l10n_ar_afip_responsibility_type_id': 1})
                        else:
                            partner_id.write({'l10n_ar_afip_responsibility_type_id': 6})
                else:
                    partner_id = partner_id[0]
                order_id = self.env['sale.order'].search([('client_order_ref','=',client_order_ref)])
                vals = {
                    'client_order_ref': client_order_ref,
                    'ml_file_id': self.id,
                    'partner_id': partner_id.id,
                    'company_id': self.env.user.company_id.id,
                    }
                if not order_id:
                    order_id = self.env['sale.order'].create(vals)
                vals_line = {
                    'product_id': product_id.id,
                    'name': prod_name or '',
                    'product_uom_qty': product_uom_qty,
                    'product_uom': product_id.uom_id.id,
                    'price_unit': price_unit,
                    'order_id': order_id.id,
                    'company_id': self.env.user.company_id.id,
                    }
                line_id = self.env['sale.order.line'].search([('order_id','=',order_id.id),('product_id','=',product_id.id)])
                if not line_id:
                    line_id = self.env['sale.order.line'].create(vals_line)
