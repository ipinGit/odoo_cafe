from odoo import api, fields, models, tools
# from odoo.exceptions import UserError, ValidationError
import logging
import re
import datetime
_logger = logging.getLogger(__name__)

class Contract(models.Model):

    _inherit = 'hr.contract'
    

    contract_statement = fields.Html('Contract Statement')
    signed_contract = fields.Binary('Signed Contract')
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string="Related User")
    sequence_id = fields.Many2one('ir.sequence', string='Numbering Sequence', help='Contract Numbering Rule')
    sequence_number_next = fields.Integer(string='Next Number',
        help='The next sequence number will be used for the next invoice.',
        compute='_compute_seq_number_next',
        inverse='_inverse_seq_number_next')
    hrd_manager = fields.Many2one('res.users', string='HRD Manager')
    date_signed = fields.Date('Date Signed')
    
    @api.multi
    # do not depend on 'sequence_id.date_range_ids', because
    # sequence_id._get_current_sequence() may invalidate it!
    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for contract in self:
            if contract.sequence_id:
                sequence = contract.sequence_id._get_current_sequence()
                contract.sequence_number_next = sequence.number_next_actual
            else:
                contract.sequence_number_next = 1

    @api.multi
    def _inverse_seq_number_next(self):
        '''Inverse 'sequence_number_next' to edit the current sequence next number.
        '''
        for contract in self:
            if contract.sequence_id and contract.sequence_number_next:
                sequence = contract.sequence_id._get_current_sequence()
                sequence.sudo().number_next = contract.sequence_number_next

    @api.model
    def create(self, vals):
        if not vals.get('sequence_id'):
            # read from xml data
            seq = self.env.ref('mas_hr.sequence_hr_contract_id')
            vals.update({'sequence_id': seq.id})
            seq._next()
        return super(Contract, self).create(vals)
    
    @api.model
    def default_get(self, default_fields):
        seq = self.env.ref('mas_hr.sequence_hr_contract_id')
        res = super(Contract, self).default_get(default_fields)
        number_next = seq.number_next_actual + seq.number_increment
        name_seq = seq.get_next_char(number_next)
        res['name'] = name_seq

        hrd_group = self.env.ref('mas_hr.group_hr_contract_hrd_manager')
        user = hrd_group.users and hrd_group.users[0]
        res['hrd_manager'] = user and user.id or False
        return res

    @api.multi
    def parse_statements(self):
        for contract in self:
            body = contract.type_id and contract.type_id.statement_body
            if body:
                list_find = re.findall('\{.*?\}', body)
                for l in list_find:
                    to_eval = l.replace('{', '').replace('}', '')
                    res = ''
                    try:
                        res = eval(to_eval)
                    except Exception as e:
                        _logger.info('EVAL error occured on executing %s ', to_eval)
                    _logger.info('type to eval===== %s, %s' %(type(res), res))
                    if isinstance(res, datetime.date):
                        res = datetime.datetime.strftime(res, '%d %b %Y')
                    if isinstance(res, int) or isinstance(res, float):
                        res = str(res)
                    res = res or '' 
                    body = re.sub(l, res, body)
                contract.contract_statement = body


class Employee(models.Model):
    _inherit = 'hr.employee'

    show_for_self = fields.Boolean('Show My Contract', compute='_compute_show_for_self')
    contracts_count2 = fields.Integer(compute='_compute_contracts_count2', string='Contract Count')
    approve_reference = fields.Boolean('Reference Approved')
    contract_duration = fields.Char(string='Work Duration')
    title = fields.Many2one('res.partner.title', string='Title', related='user_id.partner_id.title')
    recommendation_id = fields.Many2one('employee.recommendation', string='Reocommedation Form')
    recommendation_body = fields.Html('Statement Body', compute='_get_parsed_recommendation')


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

    @api.multi
    def _compute_contract_durations(self):
        for employee in self:
            deltas = []
            for contract in employee.contract_ids:
                if contract.date_end and contract.date_start:
                    timedelta = contract.date_end - contract.date_start
                    deltas.append(timedelta)
            _logger.info('============= deltas %s', deltas)
    
    @api.multi
    def _get_parsed_recommendation(self):
        for employee in self:
            if self.recommendation_id and self.recommendation_id.statement_body:
                body = self.recommendation_id.statement_body
                list_find = re.findall('\{.*?\}', body)
                for l in list_find:
                    to_eval = l.replace('{', '').replace('}', '')
                    res = ''
                    try:
                        res = eval(to_eval)
                    except Exception as e:
                        _logger.info('EVAL error occured on executing %s ', to_eval)
                    _logger.info('type to eval===== %s, %s' %(type(res), to_eval))
                    _logger.info('type to eval===== %s, %s' %(type(res), res))
                    if isinstance(res, datetime.date):
                        res = datetime.datetime.strftime(res, '%d %b %Y')
                    if isinstance(res, int) or isinstance(res, float):
                        res = str(res)
                    res = res or '' 
                    body = re.sub(l, res, body)
                employee.recommendation_body = body


class ContractType(models.Model):
    _inherit = 'hr.contract.type'

    statement_body = fields.Html('Statement Body')

class EmployeeRecomendation(models.Model):
    _name = 'employee.recommendation'

    name = fields.Char('name')
    statement_body = fields.Html('Statement Body')
    recommender = fields.Many2one('res.partner', string='Recommender')
    recommender_job = fields.Char('Recommender Position', compute='_get_recommender_position')

    @api.multi
    def _get_recommender_position(self):
        for rec in self:
            if rec.recommender:
                query = '''
                    SELECT hp.id
                    FROM res_users rs JOIN hr_employee hp ON hp.user_id = rs.id
                    WHERE rs.partner_id = %s
                ''' % (rec.recommender.id)

                self.env.cr.execute(query)
                res = self.env.cr.fetchone()
                recommender = self.env['hr.employee'].browse(res)
                rec.recommender_job = recommender and recommender.job_id and recommender.job_id.name or ''
