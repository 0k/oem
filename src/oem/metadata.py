# -*- coding: utf-8 -*-
"""ModuleMetadata manages ``__openerp__.py`` files

    >>> import kids.file as kf

Let' create a ModuleMetadata from an empty file::

    >>> metadata = kf.tmpfile()
    >>> mm = ModuleMetadata(metadata)

It's like a dict:

    >>> with mm as dct: dct  # doctest: +ELLIPSIS
    {...}

    # >>> mm['data'] = ['file1.xml']
    # You need to open the context
    >>> with mm as dct: dct['data'] = ['file1.xml']
    >>> print(kf.get_contents(metadata))
    # -*- coding: utf-8 -*-
    <BLANKLINE>
    {
        ...
        "data": [ 'file1.xml', ]...
    }
    <BLANKLINE>


# Attribute access:

#     >>> with mm as dct: dct.data.append('file2.xml')
#     >>> kf.get_contents(metadata)
#     % for key, val in ["category", ""]


    >>> kf.rm(metadata)

"""


from . import tmpl
T = tmpl.T

import kids.file as kf
from kids.data import dct
from kids.cache import cache


OPENERP_MINIMAL_DEFAULTS = {
    "name": None,
    "version": None,
    # "depends": None,
    "author": None,
    "installable": True,
    # "category": None,
    # "data": None,
    # "url": None,
    # "js": None,
    # "css": None,
    # "qweb": None,
    # "img": None,
}

TEMPLATE = tmpl.T / "__openerp__.py"


class GeneratorBasedContextManager(object):

    def context_generator(self):
        raise NotImplementedError

    def __enter__(self):
        self._context_generator = self.context_generator()
        try:
            return self._context_generator.next()
        except StopIteration:
            raise RuntimeError("context generator didn't yield")

    def __exit__(self, type, value, traceback):
        if type is None:
            try:
                self._context_generator.next()
            except StopIteration:
                return
            else:
                raise RuntimeError("context generator didn't stop")
        else:
            try:
                self._context_generator.throw(type, value, traceback)
                raise RuntimeError("generator didn't stop after throw()")
            except StopIteration:
                return True
            except:
                # only re-raise if it's *not* the exception that was
                # passed to throw(), because __exit__() must not raise
                # an exception unless __exit__() itself failed.  But
                # throw() has to raise the exception to signal
                # propagation, so this fixes the impedance mismatch
                # between the throw() protocol and the __exit__()
                # protocol.
                #
                if sys.exc_info()[1] is not value:
                    raise


def content2metadata(contents):
    if len(contents) == 0:
        contents = "{}"
    dct = OPENERP_MINIMAL_DEFAULTS.copy()
    dct.update(eval(contents))
    return dct


def metadata2content(metadata):
    defaults = OPENERP_MINIMAL_DEFAULTS.copy()
    defaults.update(metadata)
    return tmpl.render(TEMPLATE, **defaults)


class ModuleMetadata(GeneratorBasedContextManager):

    def __init__(self, metadata=False):
        self.file = metadata

    def context_generator(self):
        metadata = self.metadata
        old_metadata = dct.deep_copy(metadata)
        yield metadata
        if metadata != old_metadata:
            kf.put_contents(self.file, metadata2content(self.metadata))
            ModuleMetadata.metadata.fget.cache_clear()

    @cache(key=lambda s: s.file)
    @property
    def metadata(self):
        return content2metadata(kf.get_contents(self.file))

    def __getitem__(self, label):
        return self.metadata.__getitem__(label)

    def get(self, label, default=None):
        return self.metadata.get(label, default)

    def __getattr__(self, label):
        return self.metadata.__getitem__(label)

    def write(self):
        kf.put_contents(self.file, metadata2content(self.metadata))

    # # def __setattr__(self, label, value):
    # #     self.__setitem__(label, value)

    # def __setitem__(self, label, value):
    #     raise 
    #     if value != self._metadata[label]:
    #         self._dirty = True
    #         self._metadata[label] = value

    # def get_dict(self):
    #     for k, v in dct.metadata():
    #         self.__setitem__(k, v)

    # def update(self, dct):
    #     for k, v in dct.iteritems():
    #         self.__setitem__(k, v)

    # def flush(self, dct):
    #     if self._dirty:
    #         self.set_file_metadata(dct)
    #         self._dirty = False
    #         return True
    #     return False
