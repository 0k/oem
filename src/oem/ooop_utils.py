
import xmlrpclib
import ooop

from datetime import timedelta
from sact.epoch import Time, TzLocal, UTC
from kids.cache import cache

OOOP_NAME_TAG_LIKE_EXPR = "{%s}%%"

LoginFailed = ooop.LoginFailed


## XXXvlab: should propose a modification to OOOP code to get this
##  function accessible outside from an instanced object.
def ooop_normalize_model_name(name):
    """Normalize model name for OOOP attribute access"""
    return "".join(["%s" % k.capitalize() for k in name.split('.')])


def xmlid2tuple(xmlid, default_module=None):
    if "." in xmlid:
        return tuple(xmlid.split('.', 1))
    return default_module, xmlid


def tuple2xmlid((module, local_id), default_module=None):
    if module is None or (default_module and module == default_module):
        return local_id
    else:
        return "%s.%s" % (module, local_id)


def obj2dct(obj):
    """Gets simple displayable fields of obj in a dict"""
    dct = dict((k, getattr(obj, k)) for k, d in obj.fields.iteritems()
               if "2" not in d['ttype'])
    dct["id"] = obj._ref
    return dct


def _date_from_find_spec(spec, lapse_type):
    now = Time.now()

    count = float(spec[1:] if spec.startswith("+") or spec.startswith("-") \
                else spec)

    boundary = now - timedelta(**{lapse_type: int(count)})

    if spec.startswith("+"):
        return None, boundary
    elif spec.startswith("-"):
        return boundary, None
    else:
        return boundary, boundary + timedelta(**{lapse_type: 1})


def _ooop_filter_from_date_bounds(field_name, start, end):
    filters = {}
    if start is not None:
        filters['%s__gt' % field_name] = start.astimezone(UTC())\
                                         .strftime('%Y-%m-%d %H:%M:%S')
    if end is not None:
        filters['%s__lt' % field_name] = end.astimezone(UTC())\
                                         .strftime('%Y-%m-%d %H:%M:%S')
    return filters


def _read_string_date(str_date):
    formats = ["%Y-%m-%d",
               "%Y-%m-%d %H:%M",
               "%Y-%m-%d %H:%M:%s",
               "%m-%d",
               "%m/%d",
               "%m-%d %H:%M:%s",
               "%m-%d %H:%M",
               "%H:%M:%s",
               "%H:%M",
              ]
    for f in formats:
        try:
            return Time.strptime(str_date, f, TzLocal(), relative=True)
        except ValueError:
            pass
    raise ValueError("No format seems to know how to parse your string %r"
                     % (str_date))


def build_filters(opt_filters):
    filters = {}
    for label, value in opt_filters.iteritems():
        if not value:
            continue
        if (label.startswith('m') or label.startswith('c')) and \
           label[1:] in ["hours", "minutes", "days"]:
            date_from, date_to = _date_from_find_spec(value, label[1:])
            oe_date_field = "write_date" if label.startswith('m') \
                            else "create_date"
            filters.update(_ooop_filter_from_date_bounds(oe_date_field,
                                                        date_from, date_to))
        elif label == "model":
            filters["model"] = value
        elif label == "name":
            filters["name__like"] = value
        elif label == "tag":
            filters["name__like"] = OOOP_NAME_TAG_LIKE_EXPR % value
        elif label == "since":
            date = _read_string_date(value)
            filters.update(_ooop_filter_from_date_bounds(
                "write_date", date, None))
        elif label == "nid":
            filters["id"] = value
        else:
            filters[label] = value
    return filters


class OOOPExtended(object):
    """Adds some shortcuts to ooop"""

    def __init__(self, *args, **kwargs):
        self._ooop = ooop.OOOP(*args, **kwargs)

    def model_exists(self, model):
        """Return true if model exists in distant OOOP database"""
        return len(self._ooop.search("ir.model", [], limit=1)) != 0

    @cache
    def get_model(self, model):
        """Return OOOP Model object specified in the openerp style model

        It avoids using the CamelCased ooop style of referencing models.

        """
        return getattr(self._ooop, ooop_normalize_model_name(model))

    @cache
    def get_fields(self, model):
        """Return fields dict of current model"""

        if model in self._ooop.fields.keys():
            return self._ooop.fields[model]

        odoo_fields = self.get_model(model).fields_get()
        fields = {}
        for field_name, field in odoo_fields.items():
            field['name'] = field_name
            field['relation'] = field.get('relation', False)
            field['ttype'] = field['type']
            del field['type']
            fields[field_name] = field
        self._ooop.fields[model] = fields
        return fields

    def get_object(self, model, object_id):
        """Return OOOP Instance object using OpenERP model name

        It avoids using the CamelCased ooop style of referencing models.

        """
        return self.get_model(model).get(int(object_id))

    def write(self, *args, **kwargs):
        try:
            res = self._ooop.write(*args, **kwargs)
        except xmlrpclib.Fault, e:
            raise Exception(
                "OpenERP write error:\n" +
                ('\n'.join(
                    ["  | " + line for line in e.faultString.split('\n')])))
        return res

    def get_object_by_xmlid(self, (module, xml_id)):
        """Return OOOP Instance object using XMLid

        """
        imd = self.get_model("ir.model.data")
        lookup = imd.filter(module=module, name=xml_id)
        if len(lookup) == 0:
            return None
        lookup = lookup[0]
        return self.get_object(lookup.model, lookup.res_id)

    ## XXXvlab: should be a method of an OOOP object instance
    def get_xml_id(self, model, object_id):
        """Return module, xml_id of given object specified by its model and id.

        It avoids using the CamelCased ooop style of referencing models.

        Returns None, if there are no xml_id associated to this object.

        """
        imd = self.get_model("ir.model.data")
        lookup = imd.filter(model=model, res_id=int(object_id))
        if len(lookup) == 0:
            return None
        lookup = lookup[0]
        return lookup.module, lookup.name

    ## XXXvlab: should be a method of an OOOP object instance
    def set_xml_id(self, model, object_id, (module, xml_id)):
        imd = self.get_model("ir.model.data")
        ir_model_data = imd.new(res_id=object_id, module=module, name=xml_id)
        ir_model_data.model = model
        ir_model_data.save()

    def simple_filters(self, model, **kwargs):
        """Alternative syntax to OOOP filter

        These are simpler and dumber than the OOOP syntax. They exists
        to draw a line with CLI arguments for instances.

        They introduce some shortcuts as 'since'...

        """
        filters = build_filters(kwargs)
        return self.get_model(model).filter(**filters)

    def get_all_d(self, model, domain, order=None, limit=None, offset=0,
                  fields=[]):
        ids = self._ooop.search(model, domain, order=order,
                                limit=limit, offset=offset)
        return self._ooop.read(model, ids, fields=fields)

    def version(self):
        return tuple(self._ooop.commonsock.version()['server_version_info'])
