from odoo import api, fields, models
# from odoo.exceptions import UserError, ValidationError
import logging
import xlrd
import tempfile
import binascii

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'product.template'
    name_code = fields.Char('Name Code', compute='_get_name_code', store=True)

    @api.one
    @api.depends('name')
    def _get_name_code(self):
        self.name_code = self.name and ''.join(self.name.strip().split()).lower()


class ProductHpp(models.Model):
    _name = 'product.hpp'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=_default_currency, track_visibility='always')

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    name = fields.Char('Name')
    sale_data = fields.Binary('Sale Data')
    sale_amount = fields.Monetary(string='Total Sale', compute='compute_sale_amt')
    sale_discount = fields.Monetary(string='Total Discount', help='Total discount amount')
    sale_amount_discounted = fields.Monetary(string='Sale Discounted', help='Total sale after discount', compute='compute_salediscount')
    hpp_line_ids = fields.One2many('product.hpp.line', 'hpp_id', string='HPP Item')
    goods_consumed_ids = fields.One2many('goods.consume.line', 'hpp_id', string='HPP Item')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')])

    sale_bev_amount = fields.Monetary(string='Sale Baverages', compute='compute_sale_amt')
    sale_bev_discount = fields.Monetary(string='Sale Baverages Discount')
    sale_bev_discounted = fields.Monetary(string='Sale Baverages Discounted', compute='compute_salediscount')

    sale_food_amount = fields.Monetary(string='Sale Food', compute='compute_sale_amt')
    sale_food_discount = fields.Monetary(string='Sale Food Discount')
    sale_food_discounted = fields.Monetary(string='Sale Bar Discounted', compute='compute_salediscount')

    @api.one
    @api.depends('hpp_line_ids')
    def compute_sale_amt(self):
        amt = 0.0
        amt_food = 0.0
        for line in self.hpp_line_ids:
            recipe = self.env['product.recipe'].search([('product_id', '=', line.product_id.id)])
            if recipe:
                amt += recipe.sale_price*line.qty
                if recipe.product_id.prod_type == 'food':
                    amt_food += recipe.sale_price*line.qty

        self.sale_amount = amt
        self.sale_bev_amount = amt - amt_food
        self.sale_food_amount = amt_food

    @api.one
    @api.depends('sale_amount', 'sale_bev_discount', 'sale_food_discount')
    def compute_salediscount(self):
        self.sale_bev_discounted = self.sale_bev_amount - self.sale_bev_discount
        self.sale_food_discounted = self.sale_food_amount - self.sale_food_discount
        self.sale_discount = self.sale_bev_discount + self.sale_food_discount
        self.sale_amount_discounted = self.sale_amount - self.sale_discount

    @api.one
    def read_sale_data(self):
        if self.sale_data:
            sale_amt = 0.0
            fp = tempfile.NamedTemporaryFile(suffix=".xls")
            fp.write(binascii.a2b_base64(self.sale_data))   # self.xls_file is your binary field
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)

            for row_no in range(1, sheet.nrows):
                row = list((map(lambda row: isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no))))
                # prodname = str(row[0])
                prodname = row[0].decode('utf-8')
                prodname = ''.join(str(prodname).strip().split()).lower()
                prod_id = self.env['product.product'].search([('name_code', '=', prodname)], limit=1)
                recipe = self.env['product.recipe'].search([('product_id', '=', prod_id.id)])
                if prod_id:
                    self.env['product.hpp.line'].create({
                        'product_id': prod_id.id,
                        'qty': float(row[1]),
                        'hpp_id': self.id
                        })
                    sale_amt += recipe.sale_price*float(row[1])
            self.sale_amount = sale_amt

    def compute_raw_material(self, menu, ingre, cols):
        if ingre.ingredient_ids:
            for item in ingre.ingredient_ids:
                return compute_raw_material(menu, item, cols)
        else:
            qty = ingre.get_converted_uom()
            qty = isinstance(qty, list) and qty[0] or qty
            qty = qty*menu.qty
            if ingre.product_id.id in cols:
                qty += cols.get(ingre.product_id.id)[0]
            cols.update({ingre.product_id.id: [qty, qty*ingre.product_id.standard_price]})
            return cols


    @api.one
    def generate_consume_line(self):
        cols = {}
        for menu in self.hpp_line_ids:
            product = menu.product_id
            recipe = self.env['product.recipe'].search([('product_id', '=', product.id)])
            if not recipe:
                continue
            # for ingre in recipe.ingredient_ids:
            #     qty = ingre.get_converted_uom()
            #     qty = isinstance(qty, list) and qty[0] or qty
            #     qty = qty*menu.qty
            #     if ingre.product_id.id in cols:
            #         qty += cols.get(ingre.product_id.id)[0]
            #     cols.update({ingre.product_id.id: [qty, qty*ingre.product_id.standard_price]})
            for ingre in recipe.ingredient_ids:
                cols = compute_raw_material(menu, ingre, cols)
        for item in cols:
            goods_obj = self.env['goods.consume.line']
            # check if the product existed
            line_id = goods_obj.search([('product_id', '=', item), ('hpp_id', '=', self.id)])
            if line_id:
                line_id.update({'qty': cols.get(item)[0], 'cost': cols.get(item)[1]})
            else:
                goods_obj.create({'product_id': item, 'qty': cols.get(item)[0], 'cost': cols.get(item)[1], 'hpp_id': self.id})
        return True


class ProductHppLine(models.Model):
    _name = 'product.hpp.line'

    product_id = fields.Many2one('product.product')
    qty = fields.Integer('Qty')
    hpp_id = fields.Many2one('product.hpp')


class GoodsConsumeLine(models.Model):
    _name = 'goods.consume.line'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=_default_currency, track_visibility='always')

    product_id = fields.Many2one('product.product')
    qty = fields.Float('Qty')
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id')
    hpp_id = fields.Many2one('product.hpp')
    cost = fields.Monetary('Cost')
    prod_type = fields.Selection('Product Type', related='product_id.prod_type')
