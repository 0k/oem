# -*- coding: utf-8 -*-

import time
import re
import getpass
import socket

from kids.cache import cache
from kids.cmd import msg
from kids.ansi import aformat
from . import ooop_utils


_DEFAULT_NOT_SET = object()
_DB_REGEX = re.compile('''^
   (?P<dbname>[a-zA-Z0-9_]+)       ## db_name
   (
    @(?P<host>[a-zA-Z0-9\-_.]+)    ## optional db_host
    (
     :(?P<port>[0-9]+)           ## optional db_port
    )?
   )?
   $
''', re.VERBOSE)


class DbInstance(object):

    def __init__(self, label, cfg):
        self.label = label
        self.cfg = cfg

    @cache
    def ooop(self, lang="fr_FR", load_models=False, save_password=True):
        default_db = {
            "user": "admin",
            "password": "admin",
            "host": "localhost",
            "port": 8069,
        }
        default_db.update(self.cfg)

        ## XXXvlab: could do better than juggle around with variables
        force_query = False
        connected = False
        while not connected:
            db = self.get_creds(default_db, force_query)
            default_db.update(db)
            db = default_db
            try:
                start = time.time()
                o = ooop_utils.OOOPExtended(
                    user=db["user"], pwd=db["password"],
                    dbname=db["dbname"],
                    uri="http://%s" % db["host"], port=int(db['port']),
                    lang=lang, load_models=load_models)
                connect_duration = time.time() - start
                connected = True
            except socket.error as e:
                msg.die("Connection to %r: %s." % (db["host"], e.strerror))
            except ooop_utils.LoginFailed as e:
                if force_query is True:
                    msg.err("Access Denied. Bad Credentials ? "
                            "Trying to relog...")
                force_query = True
            except Exception as e:
                if (hasattr(e, 'faultCode') and 
                    re.search("^AccessDenied$", e.faultCode)):
                    ## seems that credentials are wrong
                    msg.err("Access Denied. Bad Credentials ? "
                            "Trying to relog...")
                    force_query = True
                elif hasattr(e, 'errcode') and e.errcode == 404:
                    msg.die("404 No openerp found on %r..."
                            % ("http://%s" % db["host"]))
                else:
                    raise

        if connect_duration > 1:
            print "profile: connect took %0.3fs" % (connect_duration, )

        if save_password:
            ## Store login and password for the next time
            changed = False
            for k, v in db.items():
                if k not in self.cfg.__cfg_global__ or \
                       self.cfg.__cfg_global__[k] != v:
                    self.cfg.__cfg_global__[k] = v
                    changed = True
            if changed:
                print(aformat("  | ", fg="green") +
                      "Saved credentials for %s in %s"
                      % (self.label,
                         self.cfg.__cfg_global__._cfg_manager._filename))
        return o

    def get_creds(self, default_db, force_query=False):
        conf_keys = default_db.keys()
        has_creds = "user" in conf_keys and "password" in conf_keys
        if not has_creds or force_query:
            print(aformat("Connecting to %s..." % self.label, fg="white", attrs=["bold", ]))
            conf = {}
            conf["user"] = raw_input(aformat("  ? ", fg="white", attrs=["bold", ]) + "Login: ")
            conf["password"] = getpass.getpass(aformat("  ? ", fg="white", attrs=["bold", ]) + "Password: ")
            return conf
        return {}


class DbManager(object):

    def __init__(self, cfg):
        self.cfg = cfg

    @cache
    def __getitem__(self, label):
        if label not in self.cfg:
            match = _DB_REGEX.search(label)
            if not match:
                raise ValueError("No database %s found, or syntax incorrect "
                                 "(use DB_NAME[@HOST[:PORT]])." % label)
            parsed_conf = dict((k, v) for k, v in match.groupdict().iteritems()
                               if v is not None)
            self.cfg.__cfg_global__[label] = parsed_conf
            print(aformat("  | ", fg="green") +
                  "New database definition for %s in %r"
                  % (label,
                     self.cfg.__cfg_global__._cfg_manager._filename))

        return DbInstance(label, self.cfg[label])

    def list(self):
        return self.cfg.keys()


class DbMixin(object):

    @cache
    @property
    def db(self):
        if "database" not in self.cfg or \
               not self.cfg["database"]:
            self.cfg.__cfg_global__["database"] = {}
        return DbManager(self.cfg["database"])



