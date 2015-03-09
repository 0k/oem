# -*- coding: utf-8 -*-

import time
import re
import getpass
import socket

from kids.cache import cache
from kids.cmd import msg

from .ooop_utils import OOOPExtended


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


class DbMixin(object):

    @cache
    @property
    def dbs_conf(self):
        """Get global db conf from config file or create an empty one."""

        if "database" not in self.cfg:
            self.cfg.__cfg_global__["database"] = {}
        return self.cfg["database"]

    def get_db_config(self, label, force_query=False):

        if not force_query and label in self.dbs_conf:
            return self.dbs_conf[label]

        match = _DB_REGEX.search(label)
        if match:
            parsed_conf = dict((k, v) for k, v in match.groupdict().iteritems()
                               if v is not None)
            print "Connecting to %s..." % label
            parsed_conf["user"] = raw_input("Login: ")
            parsed_conf["password"] = getpass.getpass()
            return parsed_conf

        raise ValueError("No database %s found, or syntax incorrect "
                         "(use DB_NAME[@HOST[:PORT]])." % label)

    @cache
    def ooop(self, label, lang="fr_FR", load_models=False):
        default_db = {
            "user": "admin",
            "password": "admin",
            "host": "localhost",
            "port": 8069,
        }
        if not hasattr(self, '_ooop'):
            self._ooop = {}
        if label not in self._ooop:
            ## XXXvlab: could do better than juggle around with variables
            force_query = False
            connected = False
            while not connected:
                db = self.get_db_config(label, force_query)
                default_db.update(db)
                db = default_db
                try:
                    start = time.time()
                    self._ooop[label] = OOOPExtended(
                        user=db["user"], pwd=db["password"],
                        dbname=db["dbname"],
                        uri="http://%s" % db["host"], port=int(db['port']),
                        lang=lang, load_models=load_models)
                    connect_duration = time.time() - start
                    connected = True
                except socket.error as e:
                    msg.die("Connection to %r: %s." % (db["host"], e.strerror))
                except Exception as e:
                    if hasattr(e, 'faultCode') and re.search("^AccessDenied$", e.faultCode):
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

            if label not in self.dbs_conf or force_query is True:
                ## Store login and password for the next time
                self.dbs_conf.__cfg_global__[label] = db
        return self._ooop[label]
