# -*- coding: utf-8 -*-

from __future__ import print_function

import os


from kids.cmd import cmd
from kids.data.mdict import mdict

from .common import OemCommand, find_root


class Command(OemCommand):
    """Oem configuration manager"""

    def _get_target_cfg(self, args, write=True, first_has_key=None):
        cfg_file_var = "%s_CONFIG_FILENAME" % args["__env__"]["name"].upper()
        if os.environ.get(cfg_file_var, False) is not False:
            if args["--global"] or args["--local"]:
                raise ValueError(
                    "``--local`` or ``--global`` are not allowed with '$%s' "
                    "set."
                    % cfg_file_var)
            return self.cfg.__cfg_head__

        if first_has_key is None:
            has_local = "local" in self.cfg.__cfg_labels__
            if not has_local and args["--local"]:
                raise ValueError(
                    "Can't access local config as you are not in a package.")
            if args["--global"] or not has_local:
                return self.cfg.__cfg_global__
            if args["--local"] or write:
                return self.cfg.__cfg_local__
            return self.cfg

        Null = object()
        ## Get first having given key
        cfg = None
        for label in ["local", "global"]:
            cfg = getattr(self.cfg, "__cfg_%s__" % label, Null)
            if cfg is Null:
                continue
            try:
                _ = mdict(cfg)[first_has_key]
                return cfg
            except KeyError:
                pass
        raise KeyError("Can't find key %r" % first_has_key)

    @cmd
    def get(self, args, key=None):
        """Display configuration values

        Usage:
          %(std_usage)s
          %(surcmd)s [--local|--global] [KEY]

        Options:
          %(std_options)s
          --local     Read only from local addon config file ``.oem.rc``,
                      If no ``--local`` nor ``--global`` is provided, the
                      result comes from all files.
                      You can't use this option if OEM_CONFIG_FILENAME
                      is defined.
          --global    Read only from global config file ``~/.oem.rc``
                      If no ``--local`` nor ``--global`` is provided, the
                      result comes from all files.
                      You can't use this option if OEM_CONFIG_FILENAME
                      is defined.

        """
        Null = object()
        cfg = self._get_target_cfg(args, write=False)
        mcfg = mdict(cfg)
        mcfg = mcfg if key is None else mcfg.get(key, Null)
        p = "%s." % key if key else ""

        if isinstance(mcfg, mdict):
            for k, v in sorted(mcfg.flat.items()):
                print("%s%s=%s" % (p, k, v))
        elif mcfg is Null:
            exit(1)
        else:
            print(mcfg)

    @cmd
    def set(self, key, value, args):
        """Display configuration values

        Usage:
          %(std_usage)s
          %(surcmd)s [--local|--global] KEY VALUE

        Options:
          %(std_options)s
          --local     Write in the local addon config file ``.oem.rc``
                      This is the default if a local repository is detected.
                      You can't use this option if %(name)s_CONFIG_FILENAME
                      is defined.
          --global    Write in the global config file ``~/.oem.rc``
                      This is the default if no local repository is detected.
                      You can't use this option if OEM_CONFIG_FILENAME
                      is defined.

        """
        cfg = self._get_target_cfg(args)
        mdict(cfg)[key] = value

    @cmd
    def rm(self, key, args):
        """Remove configuration values

        Usage:
          %(std_usage)s
          %(surcmd)s [--local|--global] KEY

        Options:
          %(std_options)sx
          --local     Remove only in local addon config file ``.oem.rc``
                      If no ``--local`` nor ``--global`` is provided, the
                      first matching place where this value is set will be
                      removed.
                      You can't use this option if %(name)s_CONFIG_FILENAME
                      is defined.
          --global    Remove only in global config file ``~/.oem.rc``
                      If no ``--local`` nor ``--global`` is provided, the
                      first matching place where this value is set will be
                      removed.
                      You can't use this option if OEM_CONFIG_FILENAME
                      is defined.

        """
        cfg = self._get_target_cfg(args, first_has_key=key)
        del mdict(cfg)[key]
