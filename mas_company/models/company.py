from odoo import api, fields, models
# from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class Company(models.Model):

    _inherit = 'res.company'

    tagline = fields.Char(string='Tagline')