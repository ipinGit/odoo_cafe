{
    'name': 'Custom Employees',
    'version': '12.0',
    'category': 'HR',
    'sequence': 99,
    'summary': 'Contracts and Salaries',
    'description': "",
    'depends': ['base', 'hr', 'hr_contract'],
    'data': [
        'views/contract_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
