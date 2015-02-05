# -*- coding: utf-8 -*-

{
    'name': '{{name}}',
    'version': '{{version}}',
    'author': '{{author}}',
    'category': '{{category}}',
    'complexity': 'normal',
{%- if website %}
    'website': '{{ website }}',
{%- endif %}
    'data': [
        'data/templates.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/view.xml',
        'actions/act_window.xml',
        'menu.xml',
        'data/data.xml',
    ],
    'depends': [
        'base',
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
