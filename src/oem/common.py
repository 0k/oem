# -*- coding: utf-8 -*-


import os
import traceback
import re

from kids.xml import xmlize, load
from kids.cmd import msg
import kids.file as kf

from . import tmpl
from .tmpl import T
from . import metadata


from .ooop_utils import build_filters, ooop_normalize_model_name, \
     obj2dct, xmlid2tuple, tuple2xmlid


def normalize_xml_filename(model, type):
    fname = file_normalize_model_name(model)
    return "%s_%s.xml" % (fname, type)


def normalize_xml_name(name, max_size=None):
    res = name.replace(".", "_")
    res = res.replace(" ", "_")
    res = re.sub(r'[^a-zA-Z0-9_]', r'', res)
    res = res.lower()
    if max_size is not None:
        res = res[0:max_size]
    return res.encode("utf-8") if isinstance(res, unicode) else res


def get_natural_sort_key(key):
    return [int(s) if s.isdigit() else s
            for s in re.split('([0-9]+)', key)]


def ooop_object_digest(obj, size=80):
    """Output a online digest of current object"""
    digest = ", ".join(["%s: %r" % (f, getattr(obj, f)
                                    if "2many" not in d['ttype']
                                    else "<*2many>")
                        for f, d in obj.fields.iteritems()])
    if len(digest) >= size:
        digest = digest[:size - 2] + ".."
    return digest


def caps_normalize_model_name(name):
    """Normalize name for python class"""
    return ooop_normalize_model_name(name)


def file_normalize_model_name(name):
    return name.replace(".", "_")


def get_refs_in_eval(source):
    """Returns list of xmlid arguments of 'ref' call in a python expression

    >>> get_refs_in_eval("ref('foo')")
    ['foo']
    >>> get_refs_in_eval("('parent_id', '=', ref('foo'))")
    ['foo']
    >>> get_refs_in_eval("('parent_id', '=', ref( \\
    ...                    'foo'))")
    ['foo']
    >>> get_refs_in_eval("(ref('bar'), '=', \\
    ...                    ref('foo'))")
    ['bar', 'foo']

    Should not catch exception if it's not parsable.

    >>> get_refs_in_eval("bar!") ## doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    SyntaxError: invalid syntax


    """
    import ast
    import token
    import symbol
    expr = ast.parse(source)

    class AstParse(object):

        def __init__(self, ast):
            self.ast = ast

        def children(self):
            return (AstParse(a) for a in ast.iter_child_nodes(self.ast))

        @property
        def fields(self):
            if not hasattr(self, "_fields"):
                setattr(
                    self, "_fields",
                    dict((k, v if not isinstance(v, ast.AST) else AstParse(v))
                         for k, v in ast.iter_fields(self.ast)))
            return getattr(self, "_fields")

        def __getitem__(self, label):
            return self.fields[label]

        def __contains__(self, label):
            return label in self.fields

        @property
        def name(self):
            return self.ast.__class__.__name__

        def is_token(self, name):
            return issubclass(type(self.ast), getattr(ast, name))

        def __repr__(self):
            return "<%s %s>" % (self.__class__.__name__, ast.dump(self.ast))

        def evaluate(self):
            code = compile(ast.Expression(self.ast),
                           '<AstParser sub expression>',
                           'eval')
            return eval(code)

    def _find_refs_in_expr(a):
        res = []
        to_parse = [a]
        while to_parse:
            e, to_parse = to_parse[0], to_parse[1:]

            if not e.name == "Call":
                to_parse.extend(e.children())
                continue

            if not e["func"].name == "Name" or \
                   e["func"]["id"] != 'ref':
                to_parse.extend(e.children())
                continue

            ## Only support direct arg
            arg = AstParse(e["args"][0])

            res.append(arg.evaluate())
        return res

    return _find_refs_in_expr(AstParse(expr))


def add_import(init_file, module_name):

    if not os.path.isfile(init_file):
        kf.put_contents(init_file, "# -*- coding: utf-8 -*-\n\nimport %s\n"
                        % module_name)
        return

    last_was_import = False
    inserted = False
    lines = []
    ## XXXvlab: could use readline
    for line in kf.get_contents(init_file).split("\n"):
        if not inserted and re.search('^import', line):
            lines.append(line)
            last_was_import = True
            continue
        if re.search('^import +%s *' % module_name, line):
            inserted = True  ## already inserted !
            break
        if last_was_import:
            lines.append("import %s" % module_name)
            last_was_import = False
            inserted = True
        lines.append(line)

    if inserted is False:
        lines.append("import %s" % module_name)
        lines.append("")

    kf.put_contents(init_file, "\n".join(lines))
    print "updated '%s'." % init_file


def _empty_data_xml():
    return xmlize(tmpl.render(T / "xml" / "main.xml", body=''))


def _new_or_existing_xml(filename):
    if os.path.isfile(filename):
        ## load existing file
        try:
            return load(filename)
        except SyntaxError, e:
            print (
                "!! Error: Can't read XML file %r.\n%s"
                % (filename, e.msg))
            exit(1)

    return _empty_data_xml()


def metadata_settings():
    dct = {
        'category': None,
        'url': None,
    }
    if os.path.isfile(get_metadata()):
        contents = kf.get_contents(get_metadata())
        dct.update(eval(contents))
    return dct


def _new_or_update_metadata(dct):
    current_dct = metadata_settings()
    old_dct = current_dct.copy()
    current_dct.update(dct)
    if current_dct != old_dct:
        defaults = {"category": None, "data": None, "url": None,
                    "js": None, "css": None, "qweb": None,
                    "active": None,
                    "img": None, "description": None, "test": None}
        defaults.update(current_dct)
        kf.put_contents(get_metadata(),
                        tmpl.render(T / "__openerp__.py", **defaults))
        print "M %r" % get_metadata()


from .db import DbMixin
from kids.cmd import BaseCommand
from kids.cache import cache


@cache(key=lambda path=None: path if path else os.getcwd())
def find_root(path=None):
    path = path if path else os.getcwd()
    metadata_path = os.path.join(path, "__openerp__.py")
    prec_path = None
    while not os.path.isfile(metadata_path) and \
              path != prec_path:
        prec_path = path
        path = os.path.dirname(path)
        metadata_path = os.path.join(path, "__openerp__.py")
    if path == prec_path:
        return False
    return path


class OemCommand(DbMixin, BaseCommand):

    @cache
    @property
    def local_path(self):
        return find_root()

    @cache
    @property
    def root(self):
        root = self.local_path
        if root is False:
            msg.die(
                "You must be in a openerp module... "
                "Did you initialise your openerp module ?\n\n"
                "    oem init  # initialise the current working "
                "directory as a openerp module.\n")
        return root

    @cache
    @property
    def metadata_file(self):
        return os.path.join(self.root, "__openerp__.py")

    @cache
    @property
    def meta(self):
        return metadata.ModuleMetadata(self.metadata_file)

    @cache
    @property
    def module_name(self):
        return os.path.basename(self.root)

    def put_contents(self, filename, contents):
        full_name = self.file_path(filename)
        if os.path.exists(full_name):
            print "  overwrite '%s'." % filename
        else:
            print "  write %r." % filename
        if isinstance(contents, unicode):
            contents = contents.encode('utf-8')
        kf.put_contents(full_name, contents)

    def add_xml(self, fname, content):
        self.put_contents(fname, content)
        with self.meta as meta:
            if fname in meta["data"]:
                return
            meta["data"].append(fname)
            print "  added %r to %r" \
                  % (fname, os.path.basename(self.metadata_file))

    def file_path(self, relpath):
        return os.path.join(self.root, relpath)

    def xmlid2tuple(self, xmlid):
        return xmlid2tuple(xmlid, self.module_name)

    def tuple2xmlid(self, t):
        return tuple2xmlid(t, default_module=self.module_name)

    def initialize(self, db, load_models=False):
        self.db_identifier = db
        self.o = self.ooop(db, load_models=load_models)

    @cache
    @property
    def xml_id_mgr(self):
        from xml_id_mgr import XmlIdManager
        return XmlIdManager(self.o, self.tracked_xml_ids.keys())
