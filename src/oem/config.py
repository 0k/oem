# -*- coding: utf-8 -*-

import os
import os.path
import sys

from kids.cache import cache


@cache
def get_conf():
    from configobj import ConfigObj
    ## XXXvlab: Should check that permission are set to
    ## protect this file in read only from user...
    exname = os.path.basename(sys.argv[0])
    if exname.endswith(".py"):
        exname = exname[:-3]
    env_var_label = ("%s_CONFIG_FILE" % exname.upper())
    if env_var_label in os.environ:
        f = os.environ[env_var_label]
    else:
        f = os.path.expanduser("~/.%s.rc" % exname)
    return ConfigObj(f)


class ConfigMixin(object):

    @cache
    @property
    def cfg(self):  ## shortcut
        return get_conf()
