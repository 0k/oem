# -*- coding: utf-8 -*-

from __future__ import print_function

import xmlrpclib
import re
import os
import os.path
import sys
import time

from kids.cmd import cmd, msg
from kids.data.lib import half_split_on_predicate
from kids.data.graph import reorder, cycle_exists
from kids.cache import cache
from kids.xml import xml2string, xmlize, load
from kids.txt import udiff


from .ooop_utils import build_filters, ooop_normalize_model_name, obj2dct, xmlid2tuple, tuple2xmlid

from .tmpl import T
from . import metadata

from . import common
from . import metadata
from . import tmpl


STATUS_DELETED = object()
STATUS_ADDED = object()
STATUS_MODIFIED = object()


def remove_tag(name, tag):
    prefix = "{%s}" % tag
    if name.startswith(prefix):
        return name[len(prefix):].strip()
    return name


class Command(common.OemCommand):
    """Record list, import to module, and other record management

    You can list, import records with this command.

    """

    @cache
    @property
    def xml_id_mgr(self):
        from .xml_id_mgr import XmlIdManager
        return XmlIdManager(self.o, self.tracked_xml_ids.keys())

    @cache
    @property
    def tracked_xml_ids(self):

        error_status = {'no_error': True}

        def err_msg(mesg):
            if error_status["no_error"]:
                print("")
                error_status["no_error"] = False
            msg.warn(mesg)

        self._tracked_files = {}
        start = time.time()
        sys.stdout.write("Loading current module's XMLs data... ")
        sys.stdout.flush()
        res = {}
        xml_files = self.meta.get('data', [])

        for xml_file in xml_files:
            if not os.path.exists(self.file_path(xml_file)):
                err_msg("file %r referenced in data section of "
                        "``__openerp__.py`` does not exists !"
                        % xml_file)
                continue
            if xml_file.endswith(".csv"):
                err_msg("skipping CSV file %r." % xml_file)
                continue
            xml = load(self.file_path(xml_file))
            self._tracked_files[xml_file] = {
                'xml_file_content': xml,
            }
            ## XXXvlab: will not catch complex situation
            file_deps = set()
            for elt in xml.getchildren():
                if elt.tag != "data":
                    continue
                for record in elt.getchildren():
                    if record.tag == "comment":
                        continue
                    if 'id' not in record.attrib:
                        err_msg("!! Error while reading %s: No id found !\n%s"
                                % (record.tag,
                                   xml2string(record, xml_declaration=False)))
                        continue
                    attrib_id = record.attrib['id']
                    deps = set()
                    if record.tag == "menuitem":
                        deps |= set(
                            xmlid2tuple(record.attrib[a],
                                        self.module_name)
                            for a in ['action', 'parent']
                            if record.attrib.get(a, False))
                    ## Get deps

                    deps |= set(
                        [xmlid2tuple(xmlid, self.module_name)
                         for xmlid in record.xpath(".//@ref")])
                    evals = record.xpath(".//@eval")
                    if evals:
                        ## must get ref() usages !
                        xmlids = []
                        for e in evals:
                            try:
                                xmlids.extend(common.get_refs_in_eval(e))
                            except Exception, exc:
                                err_msg(
                                    "WW %s: %s %s: Exception while evaluating: %r, %s"
                                    % (xml_file, record.tag, attrib_id, e, exc.msg))
                                continue
                        deps |= set(xmlid2tuple(xmlid, self.module_name)
                                    for xmlid in xmlids)

                    ## Check deps

                    for module, xmlid in deps:
                        if module != self.module_name:
                            ## Check that we depens of this module
                            if module not in self.meta['depends']:
                                self.meta['depends'].append(module)
                                err_msg("WW %s: %s %s has dependence to module %s not satisfied or explicited." \
                                        % (xml_file, record.tag, attrib_id, module))
                        else:
                            t = self.xmlid2tuple(xmlid)
                            if t not in res and not t[1].startswith("model_"):
                                err_msg("WW %s: %s %s references %s.%s which is not defined (yet?)." \
                                        % (xml_file, record.tag, attrib_id, module, xmlid))

                    res[self.xmlid2tuple(attrib_id)] = {
                        'filename': xml_file,
                        'record_xml': record,
                        'deps': deps,
                    }

                    file_deps |= deps
                    ## Check cyclicity

                    if cycle_exists(self.xmlid2tuple(attrib_id),
                                    lambda n: list(res.get(n, {'deps': []})['deps'])):
                        err_msg("WW %s: %s %s introduce a cyclic reference."
                                % (xml_file, record.tag, attrib_id))

            self._tracked_files[xml_file]["deps"] = file_deps

        if error_status["no_error"] is False:
            print("    ...", end="")
        print("done in %.3fs. (%d files, %d records)"
              % (time.time() - start, len(xml_files), len(res)))
        self._tracked_xml_ids = res
        return res

    @property
    def tracked_files(self):
        if hasattr(self, "_tracked_files"):
            return self._tracked_files
        self.tracked_xml_ids
        return self._tracked_files

    def _record_info(self, record):
        dct = obj2dct(record)
        dct["digest"] = common.ooop_object_digest(record, 50)
        xml_id = self.xml_id_mgr.lookup(record)
        dct["xml_id"] = "" if xml_id is None else self.tuple2xmlid(xml_id)
        return dct

    action_fields = ['name', 'type', 'res_model', 'view_id',
                     'view_type', 'view_mode', 'target', 'usage',
                     'domain', 'context']

    @cmd
    def import_(self, db, model,
                name=None, since=None, tag=None,
                fields=None, xmlid=None, id=None,
                all=None,
                label='%(_model)s_record',
                fmt='%(id)5s %(name)-40s %(xml_id)-40s',
                exclude_o2m=None):
        """Import records of a given model

        Usage:
          %(std_usage)s
          %(surcmd)s DB MODEL [--name NAME]
              [--since SINCE] [--tag TAG]
              [--id NID] [--xmlid XMLID]
              [--fields FIELDS]
              [--all | -a]
              [--exclude-o2m | -x]
              [--label TMPL]
              [--fmt TMPL]

        Options:
            DB               Database identifier, either an alias or a full
                             specifier: DBNAME[@HOST[:PORT]]
            --name NAME      Filter records by name (uses ``ilike`` operator)
            --since DATE     Filter records by date
            --tag TAG        Filter records by tag (XXX doc needed on that)
            --id ID          Pick record by its id
            --xmlid XMLID    Pick record by its xmlid
            --fields FIELDS  Select fields to import (use comma to separate
                             field label). Default uses predefined values.
            --all, -a        Import all matching records. Without this,
                             %(surcmd)s will complain when more than one
                             record matches given filters.
            --exclude-o2m, -x
                             Do not recurse in o2m links of target records.
            --label TMPL     Provide template for automatic file name.
                             (Default is '%%(model)s_record')
            --fmt TMPL       Provide template for command line display of
                             records when needed. This happens when more
                             than one records is selected and ``-a`` is
                             not set.
                             (Default is '%%(id)5s %%(name)-40s %%(xml_id)-40s')

        """

        self.initialize(db=db, load_models=True)

        fields = [] if not fields else fields.split(',')
        ## Should be able to set this in config file.
        fields = set(fields) - \
                 set("create_uid,write_uid,create_date,write_date".split(","))

        if not self.o.model_exists(model):
            raise ValueError("Model %r not found." % (model,))

        if xmlid:
            xmlid_tuple = self.xmlid2tuple(xmlid)
            ooop_record = self.o.get_object_by_xmlid(xmlid_tuple)
            if id:
                print("Can't use ``--xmlid`` option with ``--id`` argument !")
                sys.exit(1)
            if ooop_record is None:
                print("No object found with xmlid %r in database %s. "
                      % (self.tuple2xmlid(xmlid_tuple), db))
                sys.exit(1)
            if model != ooop_record._model:
                print("Object found with xmlid %r has model %s not model %s. "
                      % (self.tuple2xmlid(xmlid_tuple),
                         ooop_record._model, model))
                sys.exit(1)
            model = ooop_record._model
            id = ooop_record._ref

        kwargs = {
            "name": name,
            "since": since,
            "id": id, "tag": tag,
        }
        l = self.o.simple_filters(model, **kwargs)

        if len(l) == 0:
            print("Filter %r yielded no matching "
                  "candidate view." % build_filters(kwargs))
            sys.exit(1)
        if len(l) != 1:
            if not all:
                exact_matches = [r for r in l
                                 if getattr(r, 'name', False) == name]
                if len(exact_matches) != 1:
                    print("View name filter %r yielded too much matching "
                          "candidate views:\n" % build_filters(kwargs))
                    for r in l:
                        print(fmt % self._record_info(r))
                    sys.exit(1)

                l = exact_matches

        self._record_import(l, label, fields, tag,
                            follow_o2m=not exclude_o2m)

    def _get_file_name_for_record(self, ooop_record, import_data,
                                  label="%(_model)s_record"):
        model = ooop_record._model
        dct = obj2dct(ooop_record)
        dct["_model"] = model[2:] if model.startswith('x_') else model
        f = label % dct
        return "%s.xml" % common.file_normalize_model_name(f)

    def _record_import(self, ooop_records, label, fields, tag,
                       follow_o2m=True):

        content = []
        for ooop_record in ooop_records:
            print("Importing record %s,%d: %s" %
                  (ooop_record._model, ooop_record._ref,
                   ("(name=%r)" % ooop_record.name)
                   if 'name' in ooop_record.fields else ''))

            content += self.to_xml([ooop_record], fields,
                                   follow_o2m=follow_o2m, tag=tag)

        ## This should be done directly in arch field in mako template
        # content = [(r, re.sub(r'\bx_([a-zA-Z_]+)\b', r'\1', c))
        #            for r, c in content]
        xmls = [(r, xmlize(c), d) for r, c, d in content]

        records_written = []
        filenames = {}
        for record, xml, deps in xmls:
            records_written.append(record)
            xmlid = self.xml_id_mgr.lookup(record)
            if xmlid in self.tracked_xml_ids:
                elt = self.tracked_xml_ids[xmlid]['record_xml']

                filename = self.tracked_xml_ids[xmlid]['filename']
                if xml2string(elt) == xml2string(xml):
                    print("  noop: %s stored in %s" % (self.tuple2xmlid(xmlid),
                                                       filename))
                    continue
                print("  modified: %-65r" % (self.tuple2xmlid(xmlid), ))
                if filename not in filenames:
                    filenames[filename] = \
                        self.tracked_files[filename]['xml_file_content']
                ## find 'data' element (parent) of tracked xml
                elt = self.tracked_xml_ids[xmlid]['record_xml']
                data = elt.getparent()
                data.replace(elt, xml)
                self.tracked_xml_ids[xmlid]['record_xml'] = xml
                self.tracked_xml_ids[xmlid]['replaced'] = \
                    self.tracked_xml_ids[xmlid].get('replaced', 0) + 1
            else:
                print("  added: %-65r" % (self.tuple2xmlid(xmlid), ))
                filename = self._get_file_name_for_record(record, xmls, label)
                if filename not in filenames:
                    filenames[filename] = \
                        self.tracked_files[filename]['xml_file_content'] \
                        if filename in self.tracked_files else \
                        common._empty_data_xml()
                ## find 'data' xml element.
                data = filenames[filename].getchildren()[0]
                data.append(xml)

        if filenames:
            print("Writing changes:")
        else:
            print("No changes to write to files.")

        for filename, data in filenames.iteritems():
            self.add_xml(filename, xml2string(data))

        for r in records_written:
            self._trigger_event(r, 'write')

    def menu_to_xml(self, menu, xml_id, fields=None,
                    follow_o2m=False, tags=False):
        content = []
        action = None
        action_xml_id = None
        deps = []

        if menu.action:
            action = self.o.get_object(*menu.action.split(","))
            omodel = action.res_model
            lookup_action = self.xml_id_mgr.lookup(action._model, action._ref)
            if lookup_action is None:
                ## we'll then try to import action also
                content.extend(self.to_xml(
                    [action],
                    fields=self.action_fields,
                    follow_o2m=True))
                lookup_action = self.xml_id_mgr.lookup(action._model,
                                                       action._ref)
                assert lookup_action is not None
            deps.append(lookup_action)
            action_xml_id = self.tuple2xmlid(lookup_action)

        _module, xml_id = self.xml_id_mgr.create(
            self.module_name,
            menu._model, menu._ref, menu.name)
        if menu.parent_id:
            lookup_menu = self.xml_id_mgr.lookup(menu.parent_id._model,
                                                 menu.parent_id._ref)
            if lookup_menu is None:
                print("  !! no xml id for parent menu %r (%s,%s) of menu %r"
                      % (menu.parent_id.name, menu.parent_id._model,
                         menu.parent_id._ref, menu.name))
                parent_xml_id = False
            else:
                deps.append(lookup_menu)
                parent_xml_id = self.tuple2xmlid(lookup_menu)
        else:
            parent_xml_id = False
        groups = False
        if menu.groups_id:
            groups = []
            for g in menu.groups_id:
                lookup_xml_id = self.xml_id_mgr.lookup(g._model, g._ref)
                if lookup_xml_id is None:
                    ## we'll then try to import this menu also
                    content.extend(self.to_xml(
                        [g], fields=[f[0] for f in fields],
                        follow_o2m=True, tag=tags))
                    lookup_xml_id = self.xml_id_mgr.lookup(g._model, g._ref)
                    assert lookup_xml_id is not None
                deps.append(lookup_xml_id)
                groups.append(lookup_xml_id)
            groups = ",".join([self.tuple2xmlid(lookup_xml_id)
                               for lookup_xml_id in groups])

        content.append(
            (menu,
             tmpl.render(
                 tmpl.OPENERP_MENU_TEMPLATE,
                 xml_id=xml_id,
                 m=menu, action=action,
                 action_xml_id=action_xml_id,
                 groups=groups,
                 parent_xml_id=parent_xml_id,
                 file_normalize_model_name=common.file_normalize_model_name),
             deps))
        return content

    def to_xml(self, records, fields=None, follow_o2m=False, tag=False):
        content = []
        objs = [(record, record._model, getattr(record, 'name', 'anonymous'))
                for record in records]
        while objs:
            (r, model, identifier), objs = objs[0], objs[1:]

            exported_fields = list((k, v) for k, v in r.fields.iteritems()
                                   if not fields or k in fields)

            ## force 'name', then 'sequence' to be first field displayed...
            order_rank = {"name": 0, "sequence": 1}
            exported_fields.sort(key=lambda x: order_rank.get(x[0], x[0]))

            ## XXXvlab: Warning, nothing is done to ensure uniqueness within
            ## the current XML. Hopefully, names will distinguish them out.
            lookup = self.xml_id_mgr.lookup(r)
            if lookup:
                module, xml_id = lookup
            else:
                module, xml_id = self.xml_id_mgr.create(
                    self.module_name,
                    model, r._ref, identifier)
                self.o.set_xml_id(model, r._ref, (module, xml_id))

            ##
            ## Remove markups (tags) and set xml_id in current database
            ##

            if tag and 'name' in r.fields:
                ## change only in current lang
                r.name = remove_tag(r.name, tag)

                def _save(r):
                    lang = self.o.context.get('lang', 'en_US')
                    if lang != 'en_US':
                        old_lang = self.o.context['lang']
                        del self.o.context['lang']
                        ## save only the name attribute to avoid overwriting
                        ## other values
                        current_name = self.o.read(r._model, r._ref,
                                                   ['name']).get('name', None)
                        if current_name is not None:
                            new_name = remove_tag(current_name, tag)
                            self.o.write(r._model, [r._ref],
                                         {'name': new_name})
                            print("  renamed object %r in %r (new name: %r)"
                                  % (r, 'en_US', new_name))
                        self.o.context['lang'] = old_lang
                    try:
                        ## save only the name attribute to avoid overwriting
                        ## other values
                        self.o.write(r._model, [r._ref], {'name': r.name})
                        print("  renamed object %r in %r (new name: %r)"
                              % (r, lang, r.name))
                    except xmlrpclib.Fault, e:
                        if re.search("^warning -- Constraint Error.*"
                                     "Language code.*known languages",
                                     e.faultCode, re.DOTALL):
                            pass
                            #print("  warning: current database does not support language %r" % self.o.context['lang'])
                        else:
                            raise

                self._add_callback(r, 'write', _save)

            ##
            ## Generate XML for a record
            ##

            if model == "ir.ui.menu":
                content.extend(self.menu_to_xml(
                    r, xml_id, exported_fields,
                    follow_o2m=follow_o2m))
            else:
                content.extend(self.record_to_xml(
                    r, xml_id, exported_fields, tag=tag))
            if follow_o2m:
                ## Add all the one2many:
                for f, fdef in exported_fields:
                    if fdef['ttype'] == 'one2many' and getattr(r, f):
                        ## big mess to get the element that do not have any
                        ## xml_id to the end of a classical sort.
                        with_xmlids, without_xmlids = half_split_on_predicate(
                            getattr(r, f),
                            lambda obj: self.xml_id_mgr.lookup(obj) is None)
                        with_xmlids.sort(key=self.xml_id_mgr.get_xml_id_sort_key)
                        print("adding o2m descendant along %r attribute" % f)
                        objs += [(obj, fdef['relation'], identifier)
                                 for obj in (with_xmlids + without_xmlids)]
        return content

    def record_to_xml(self, record, xml_id, fields=None, tag=False):
        return self._render_record_template(record, record._model, xml_id, fields=fields)

    def _render_record_template(self, r, model, xml_id, fields=None):
        deps = []
        ## XXXvlab: couldn't we remove ``model`` in favor of r._model ?
        return [(r, tmpl.render(T / "xml" / "record.xml",
                                r=r, fields=fields,
                                model=model,
                                xml_id=xml_id,
                                xml_id_mgr=self.xml_id_mgr,
                                db_identifier=self.db_identifier,
                                deps=deps), deps)]

    ## XXXvlab: should be a method of an ooop.Data adapter
    def _add_callback(self, r, event, callback):
        if not hasattr(self, 'cbs'):
            self.cbs = {}

        key = (r._model, r._ref)

        if not key in self.cbs:
            self.cbs[key] = {}

        record_events = self.cbs[key]

        if not event in record_events:
            record_events[event] = []

        record_events[event].append((r, callback))

    ## XXXvlab: should be a method of an ooop.Data adapter
    def _trigger_event(self, r, event):
        key = (r._model, r._ref)
        events = getattr(self, "cbs", {}).get(key, {}).get(event, [])
        for r, ev in events:
            ev(r)

    def __missing__(self, name):
        return ('Command %r does not exist' % name,)

    def __exit__(self, etype, _exc, _tb):
        "Will be called automatically at the end of the intepreter loop"
        if etype not in (None, GeneratorExit):  # success
            import traceback
            print(traceback.print_tb(_tb))
            print("Failure: %s" % _exc)
            sys.exit(1)
