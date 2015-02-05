import os.path
import sys
import kids.file as kf

import mako.template
import mako.exceptions

from kids.xml import quote_attr, quote_value
from kids.file.chk import exists, is_dir
from kids.cache import cache


BASE_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "templates")


PY_FILE_TEMPLATE_COLUMNS_PART = """\\
   % for f in sorted(fields):
        <%
        fname = f.name
        if fname.startswith('x_'):
            fname = fname[2:]
        %>
        '${fname}': fields.${f.ttype}(
        % if f.ttype == 'many2one' or f.ttype == 'one2one':
            '${f.relation}',
        % endif
        % if f.ttype == 'one2many':
            '${f.relation}',
            '${f.relation_field}',
        % endif
        % if f.ttype == 'many2many':
            '${f.relation}',
            rel="TABLE NAME", ## TO EDIT
            id1="ID1",
            id2="ID2",
        % endif
            string=${_pa(f.field_description)},
        % if f.ttype == 'char':
            size=${f.size},
        % endif
        % if f.required:
            required=True,
        % endif
        % if f.readonly:
            readonly=True,
        % endif
        % if f.selection != '' and f.selection != False:
            selection=${repr(f.selection)},
        % endif
        % if f.domain != '[]' and f.domain:
            domain=${repr(f.domain)},
        % endif
        % if f.translate is not False:
            translate=${repr(f.translate)},
        % endif
        ),
    % endfor
"""

PY_FILE_TEMPLATE = """\\
# -*- coding: utf-8 -*-

from osv import osv, fields


class ${class_name}(osv.osv):

    _name = '${name}'
    % if inherit:
    _inherit = ${repr(inherit)}
    % endif

    _columns = {
     ${columns}
    }

    _defaults = {
        ## Not implemented yet
    }


${class_name}()  ## required in 6.0, but optional in >6.1
"""


OPENERP_MENU_TEMPLATE = '''
<menuitem id=${_pa(xml_id)}
          name=${_pa(m.name)}
% if parent_xml_id:
          parent=${_pa(parent_xml_id)}
% endif
% if m.sequence is not None:
          sequence="${m.sequence}"
% endif
% if action_xml_id is not None:
          action=${_pa(action_xml_id)}
% endif
          />

'''


OPENERP_VIEW_TEMPLATE = '''\\
<%

xml_id = v.xml_id or ("view_%s" % file_normalize_model_name(v.name))

%>\\
<record id="${xml_id}" model="ir.ui.view">
  <field name="name">${v.name}</field>
  <field name="model">${model}</field>
  % if v.inherit_id:
  <field name="inherit_id" ref="${v.inherit_id.xml_id}"/>
  % endif
  <field name="type">${v.type}</field>
  <field name="priority">${v.priority}</field>
  <field name="arch" type="xml">${arch}</field>
</record>
'''


class Registry(object):
    """Convenience browseable store for templates

    Maps a directory to easily accessible templates:

    >>> base = Registry()
    >>> base / 'xml'
    <oem.tmpl.Registry object at ...>
    >>> base / '__openerp__.py'
    <mako.template.Template object at ...>

    """

    def __init__(self, base=None):
        if base is None:
            base = BASE_TEMPLATE_PATH
        self.base = base

    def __div__(self, label):
        realpath = os.path.join(
            self.base,
            "%s" % label)
        if is_dir(realpath):
            return Registry(realpath)
        ## XXXvlab: conflict could occur if a dir is name LABEL and
        ## file is named LABEL.tpl
        tpl_realpath = realpath + ".tpl"
        if exists(tpl_realpath):
            return mk(kf.get_contents(tpl_realpath))
        raise KeyError("File %r not found" % tpl_realpath)


T = Registry()


def output_message(msg):
    sys.stderr.write(msg + "\n")


GLOBAL_MAKO_ENV = {
    '_pa': quote_attr,
    '_pv': quote_value,
    'msg': output_message
}

@cache
def mk(text):
    """Build a Mako template.

    This template uses UTF-8 encoding

    """
    # default_filters=['unicode', 'h'] can be used to set global filters
    return mako.template.Template(
        text,
        input_encoding='utf-8',
        output_encoding='utf-8',
        strict_undefined=False)


def render(tpl, **kwargs):
    if not isinstance(tpl, mako.template.Template):
        tpl = mk(tpl)
    env = GLOBAL_MAKO_ENV.copy()
    env.update(kwargs)
    try:
        return tpl.render(**env)
    except Exception, e:
        error_txt = mako.exceptions.text_error_template().render().strip()
        raise SyntaxError(
            ("Template rendering error: %s\n  | " % e.message) +
            "\n  | ".join([l for l in error_txt.split("\n")]))
