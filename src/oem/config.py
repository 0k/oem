# -*- coding: utf-8 -*-

import kids.cfg

from kids.cache import cache
from kids.data import mdict


load = kids.cfg.load


class ConfigMixin(object):

    @cache
    @property
    def cfg(self):  ## shortcut
        if self.has_root:
            return kids.cfg.load(local_path=self.root)
        else:
            return kids.cfg.load()

    @cache
    @property
    def mcfg(self):  ## shortcut
        return mdict.mdict(self.cfg)
