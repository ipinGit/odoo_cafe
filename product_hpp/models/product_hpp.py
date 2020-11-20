from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProductRecipe(models.Model):
    _name = 'product.recipe'

    ingredient_ids = fields.One2many('product.ingredient', 'recipe_ref', string='Product Ingredients')
    hpp = fields.Float(string='HPP(%)', compute='_compute_hpp')
    hpp_cost = fields.Float(string='HPP', compute='_compute_hpp')
    product_id = fields.Many2one('product.template', string='Related Product', domain=[('sale_ok', '=', True)])
    name = fields.Char('Name')
    recipe_type = fields.Selection([('food', 'Food'), ('beverage', 'Beverage')], string='Recipe Type', default='food')

    sale_price = fields.Float(string='Sale Price')

    @api.one
    @api.depends('ingredient_ids', 'ingredient_ids.cost', 'sale_price')
    def _compute_hpp(self):
        for r in self:
            r.hpp_cost = sum([r.cost for r in r.ingredient_ids])
            r.hpp = r.sale_price and r.hpp_cost/r.sale_price*100.0 or 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.name = self.product_id.name and self.product_id.name + ' Recipe'


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    conversion_ids = fields.One2many('product.conversion', 'product_id', string='Conversion Table')
    prod_type = fields.Selection([('food', 'Food'), ('beverage', 'Beverage')], string='Product Type',
                                 help='Select to what division this product belogs to', default='food')


# class Product(models.Model):
#     _inherit = 'product.template'

#     conversion_ids = fields.One2many('product.conversion', 'product_id', string='Conversion Table')


class ProductIngredient(models.Model):
    _name = 'product.ingredient'

    recipe_ref = fields.Many2one('product.recipe', string='Reference Recipe')
    product_id = fields.Many2one('product.template', string='Product Ingredient', domain=[('purchase_ok', '=', True)], required=True)
    qty = fields.Float('Quantity', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    cost = fields.Float('Cost')

    @api.onchange('qty', 'product_id', 'uom_id')
    def _onchange_qty(self):
        _logger.info('================= %s -- %s -- %s ' % (self.product_id, self.qty, self.uom_id))
        if self.product_id and self.qty and self.uom_id:
            for c in self.product_id.conversion_ids:
                _logger.info('conversion == %s', c.factor)
            factor_from = self.env['product.conversion'].search([('product_id', '=', self.product_id.id), ('uom_id', '=', self.uom_id.id)], limit=1)
            factor_to = self.env['product.conversion'].search([('product_id', '=', self.product_id.id), ('uom_id', '=', self.product_id.uom_id.id)], limit=1)
            _logger.info('================= %s, = =  %s ' % (factor_to, factor_from))

            self.cost = factor_from and factor_to and 1.0*factor_to.factor/factor_from.factor*self.product_id.standard_price*self.qty or 0.0


class UomConvertion(models.Model):
    _name = 'product.conversion'

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    factor = fields.Float('Factor')
    product_id = fields.Many2one('product.template', string='Reference Product')
    # product_tpl_id = fields.Many2one('product.template', string='Reference Product')
