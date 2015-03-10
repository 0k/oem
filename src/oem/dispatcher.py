# -*- coding: utf-8 -*-


from kids.cache import cache


@cache
def parse_dispatch_specs(outfile_cli):
    """Return internal spec from CLI string field spec

        >>> from pprint import pprint as pp

    Model attribution
    -----------------

    Syntaxes uses MODEL:PATH

        >>> pp(parse_dispatch_specs('model:/foo/bar'))
        {'model': '/foo/bar'}

    But if you don't specify the model, it'll be all models::

        >>> pp(parse_dispatch_specs('/foo/bar'))
        {'*': '/foo/bar'}

    Chaining Model attribution
    --------------------------

    You can use the previous syntax several times separated with ';' to give
    multiple model attributions::

        >>> pp(parse_dispatch_specs('model:/foo/bar;/foo/wiz'))
        {'*': '/foo/wiz', 'model': '/foo/bar'}

    When '*' string is used as a model, this is for all the records. Rules
    will use this spec as a basis and then use any other specific specs as
    additional info::

        >>> pp(parse_dispatch_specs('*:/foo/bar'))
        {'*': '/foo/bar'}

    Path parsing and rules
    ------------------------

    Multiple spec on the same model concats::

        >>> pp(parse_dispatch_specs('foo:/foo;foo:/bar'))
        {'foo': '/bar'}

    Empty string is empty spec::

        >>> pp(parse_dispatch_specs(''))
        {}

    """
    specs = {}
    for model_spec in outfile_cli.split(";"):
        if not model_spec:
            continue
        if ":" not in model_spec:
            model = '*'
            fields_spec = model_spec
        else:
            model, fields_spec = model_spec.split(':')
        specs[model] = fields_spec
    return specs


class BasicFileDispatcher(object):
    """Dispatch XML records to files.

    This dispatcher takes a dict as config, and will output records
    depending on their model.

    """

    def __init__(self, opts):
        self.opts = opts

    def __call__(self, record):
        """Returns full path to store the given record."""

        model = record.get('_model')
        fp = self.opts.get(
            model, self.opts.get('*', '%(_model_underscore)s_records.xml'))
        if '%' in fp:
            dct = record.copy()
            dct["_model_underscore"] = model.replace(".", "_")
            fp = fp % dct
        return fp
