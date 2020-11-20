{
    'name': 'Product HPP and Receipt',
    'version': '12.0',
    'category': 'Product',
    'sequence': 99,
    'summary': 'Add functionality to show HPP based on Ingredient Items',
    'description': "",
    'depends': ['product'],
    'data': [
        'data/hpp_group.xml',
        'views/product_hpp_view.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
