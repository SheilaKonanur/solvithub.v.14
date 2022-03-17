# -*- coding: utf-8 -*-
{
    'name': "SolvitHub Registry",
    'version': '13.0.1.0.1',
    'summary': """Registring Services""",
    'category': 'Human Resources',
    'description': """
        Registry form.
    """,

    'author': "The Office BPO",
    'license': 'LGPL-3',
    'company': 'The OfficeBPO',
    'maintainer': 'The OfficeBPO',
    'support': 'apps.admin@theofficebpo.com',
	'website': 'www.solvithub.com',
    'demo': [],

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_recruitment', 'contacts', 'web'],

    # always loaded
    'data': [
        # 'data/parameters.xml',
        'views/res_config_settings_view.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [
    ],
    'application': True,
    'sequence': 1,
}