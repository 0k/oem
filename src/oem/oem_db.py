# -*- coding: utf-8 -*-


from kids.cmd import cmd

from .common import OemCommand


class Command(OemCommand):
    """Manage OpenERP/Odoo remote connections

    """

    @cmd
    def use(self, args, db=None):
        """Declare database as the default for following operation.

        Usage:
          %(std_usage)s
          %(surcmd)s [--local|--global] [DB]

        Options:
          %(std_options)s
          --local     Sets default db in local config file ``.oem.rc``,
                      By default, this is not selected.
                      You can't use this option if OEM_CONFIG_FILENAME
                      is defined.
          --global    Sets default db in global config file ``~/.oem.rc``
                      If no ``--local`` nor ``--global`` is provided, the
                      default is ``--global``.
                      You can't use this option if OEM_CONFIG_FILENAME
                      is defined.

        """

        if db is None:
            print self.cfg["default_db"]
            return
        from .oem_config import Command as CfgCommand
        config_set = CfgCommand().set
        if not args["--local"]:
            args["--global"] = True
        config_set("default_db", db, args)

    @cmd
    def list_(self):
        """List configured databases

        Usage:
          %(std_usage)s
          %(surcmd)s list

        Options:
          %(std_options)s

        """

        for label in self.db.list():
            db = self.cfg["database"][label]
            print("%-32s %-32s (user: %s)"
                  % (label,
                     "%s@%s%s" % (
                         db["dbname"], db["host"],
                         (":%s" % db["port"]) if "port" in db else ""),
                     db["user"]))

    @cmd
    def add(self, label, dbname, host="localhost", port=8069,
            user="admin", password="admin"):
        """Add a database configuration

        Usage:
          %(std_usage)s
          %(surcmd)s LABEL DBNAME [--host HOST] [--port PORT]
              [--user USER] [--password PASSWORD]

        Options:
          %(std_options)s
          LABEL                 Identifier for the connection.
          DBNAME                Database name
          --host HOST           IP or fqdn of OpenERP/Odoo host instance.
                                (Default is 'localhost')
          --port PORT           Port used by HOST to server OpenERP/Odoo.
                                (Default is 8069)
          --user USER           User to log authenticate with on OpenERP/Odoo.
                                (Default is "admin")
          --password PASSWORD   Password to authenticate with on OpenERP/Odoo.
                                (Default is "admin")

        """
        db_cfg = self.cfg["database"]
        if label in db_cfg:
            db = db_cfg[label]
            raise ValueError(
                "Database %r already configured to %s@%s (user: %s)"
                % (label, db["dbname"], db["host"], db["user"]))
        db_cfg.__cfg_global__[label] = {
            "host": host,
            "user": user,
            "password": password,
            "dbname": dbname,
            "port": port
        }

        # print("Added %r to the configured database." % label)

    @cmd
    def rm(self, label):
        """Remove database configuration

        Usage:
          %(std_usage)s
          %(surcmd)s LABEL

        """

        db_cfg = self.cfg["database"]
        if label not in db_cfg:
            raise ValueError("No database %s found." % label)

        del db_cfg.__cfg_global__[label]

        # print("Removed %r to the configured database." % label)
