# -*- coding: utf-8 -*-

from common import normalize_xml_name, get_natural_sort_key


XMLID_MAXSIZE = 128


class XmlIdManager(object):
    """Manages creation and lookup of xml_id in OOOP database or XML files"""

    def __init__(self, ooop_instance, file_xml_ids):
        self.ooop = ooop_instance
        self._xml_ids = {}
        self._file_xml_ids = file_xml_ids[:]

    def get_xml_id_sort_key(self, obj):
        """return a sort key for objects"""
        lookup = self.lookup(obj)
        if lookup is None:
            return None
        return get_natural_sort_key(lookup[1])

    def lookup(self, model_or_obj=None, res_id=None):
        if not(isinstance(model_or_obj, basestring)):
            res_id = model_or_obj._ref
            model = model_or_obj._model
        else:
            model = model_or_obj
        if (res_id, model) in self._xml_ids:
            return self._xml_ids[(res_id, model)]
        return self.ooop.get_xml_id(model, res_id)

    def create(self, module, model, res_id, seed_name):
        lookup = self.lookup(model, res_id)
        if lookup:
            ## Object already existent
            return lookup

        ## local names
        all_names = [n for (m, n) in self._xml_ids.values()
                     if m == module]
        ## distant names
        ## XXXvlab: could cache these results
        objs = self.ooop.IrModelData.filter(module=module, model=model)
        all_names += [obj.name for obj in objs]
        all_names += self._file_xml_ids
        all_names = set(all_names)

        i = 0
        model_normalized = normalize_xml_name(model)
        seed_normalized = normalize_xml_name(
            seed_name,
            max_size=XMLID_MAXSIZE - 10 - len(model_normalized))
        name = "%s_%s_r%d" % (model_normalized, seed_normalized, i)
        while name in all_names:
            i += 1
            name = "%s_%s_r%d" % (model_normalized, seed_normalized, i)
        ## add xml_id to cache.
        print "  generated xml_id for model: %r, id: %r => xml_id: %r" \
              % (model, res_id, name)
        self._xml_ids[(res_id, model)] = (module, name)
        return module, name
