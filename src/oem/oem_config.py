# -*- coding: utf-8 -*-

from __future__ import print_function

from kids.cmd import cmd
from kids.data.mdict import mget, mset, mdel

from .common import OemCommand


def show_config(c, prefix=""):
    if c is None:
        raise StopIteration
    if not isinstance(c, dict):
        yield c
        raise StopIteration
    p = "" if prefix == "" else "%s." % prefix
    for k, v in c.iteritems():
        if isinstance(v, dict):
            for line in show_config(v, prefix="%s%s" % (p, k)):
                yield line
        else:
            yield "%s%s=%s" % (p, k, v)


class Command(OemCommand):
    """Oem configuration manager"""

    @cmd
    def get(self, key=None):
        """Display configuration values

        Usage:
          %(std_usage)s
          %(surcmd)s [KEY]

        Options:
          %(std_options)s

        """
        cfg = mget(self.cfg, key)

        for line in show_config(cfg, prefix=key or ""):
            print(line)

    @cmd
    def set(self, key=None, value=None):
        """Display configuration values

        Usage:
          %(std_usage)s
          %(surcmd)s KEY VALUE

        Options:
          %(std_options)s

        """

        mset(self.cfg, key, value)
        self.cfg.write()

    @cmd
    def rm(self, key=None):
        """Remove configuration values

        Usage:
          %(std_usage)s
          %(surcmd)s KEY

        Options:
          %(std_options)s

        """

        mdel(self.cfg, key)
        self.cfg.write()
