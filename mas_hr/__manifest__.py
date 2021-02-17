{
    'name': 'Custom Employees',
    'version': '12.0',
    'category': 'HR',
    'sequence': 99,
    'summary': 'Contracts and Salaries',
    'description': "",
    'depends': ['base', 'hr', 'hr_contract', 'mas_company'],
    'data': [
        'views/contract_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hr_data.xml',
        'report/contract.xml',
        'report/recommendation.xml',
        'report/report.xml',
        
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
