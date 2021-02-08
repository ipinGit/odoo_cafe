from odoo import api, fields, models
# from odoo.exceptions import UserError, ValidationError
import logging

class Contract(models.Model):

    _inherit = 'hr.contract'
    
    contract_statement = fields.Html('Contract Statement')
    signed_contract = fields.Binary('Signed Contract')
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string="Related User")
    

class Employee(models.Model):
    _inherit = 'hr.employee'

    show_for_self = fields.Boolean('Show My Contract', compute='_compute_show_for_self')
    contracts_count2 = fields.Integer(compute='_compute_contracts_count2', string='Contract Count')

    @api.multi
    def _compute_show_for_self(self):
        # show_leaves = self.env['res.users'].has_group('hr_holidays.group_hr_holidays_user')
        for employee in self:
            if employee.user_id == self.env.user:
                employee.show_for_self = True
            else:
                employee.show_for_self = False

    def _compute_contracts_count2(self):
        # read_group as sudo, since contract count is displayed on form view
        contract_data = self.env['hr.contract'].sudo().read_group([('employee_id', 'in', self.ids)], ['employee_id'], ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in contract_data)
        for employee in self:
            employee.contracts_count2 = result.get(employee.id, 0)

