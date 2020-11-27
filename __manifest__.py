{
    'name': 'Odoo Site Search App',
    'version': '13.0.1.0',
    'license': 'LGPL-3',
    'category': 'Website',
    'summary': 'Boost conversions and sales with a smart and all-powerful site search platform.',
    'description': "",
    'website': 'https://sitesearchapp.com',
    'author': 'SCI Global Services Inc.',
    'depends': ['website', 'portal', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/templates.xml',
        'views/sitesearchapp.xml',
        'views/res_config.xml',
        'data/cron.xml'
    ],
    'images': ['static/description/banner.gif'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
