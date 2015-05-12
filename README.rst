=========================
oem
=========================

.. image:: http://img.shields.io/pypi/v/oem.svg?style=flat
   :target: https://pypi.python.org/pypi/oem/
   :alt: Latest PyPI version

.. image:: http://img.shields.io/pypi/dm/oem.svg?style=flat
   :target: https://pypi.python.org/pypi/oem/
   :alt: Number of PyPI downloads

.. image:: http://img.shields.io/travis/0k/oem/master.svg?style=flat
   :target: https://travis-ci.org/0k/oem/
   :alt: Travis CI build status

.. image:: http://img.shields.io/coveralls/0k/oem/master.svg?style=flat
   :target: https://coveralls.io/r/0k/oem
   :alt: Test coverage


``oem`` is a command line tools to help OpenERP/Odoo module makers and
server administrator on common generic tasks.


Maturity
========

Do not use this software for now. These are the first alpha releases.


Features
========

using ``oem``:

- ``oem init`` allows you to create skeletin of new project easily
- ``oem rec import`` manage your XML data files easily by importing UI modifications.


Compatibility
=============

This code is python2 only for now.


Installation
============

..
   You don't need to download the GIT version of the code as ``oem`` is
   available on the PyPI. So you should be able to run::

       pip install oem

Classical python libraries dependencies can be installed on debian-like system::

    apt-get update && apt-get install python-pip python-dev libxml2-dev libxslt1-dev libz1g-dev

For now, because we use specific ``cookiecutter`` and ``ooop`` versions,
you should make sure you have the correct dependencies::

    pip install -r requirements.txt

And then you can use directly the ``oem`` link, or install it locally::

    python setup.py install



..
   If you have downloaded the GIT sources, then you could add install
   the current version via traditional::


..
   And if you don't have the GIT sources but would like to get the latest
   master or branch from github, you could also::

       pip install git+https://github.com/0k/oem

   Or even select a specific revision (branch/tag/commit)::

       pip install git+https://github.com/0k/oem@master


Usage
=====


oem rec import
--------------

This command imports records from a running OpenERP/Odoo database to
XML records that it'll dispatch in files in your module hierarchy to
follow conventions. It takes care also, of declaring any new files in
the ``data`` section of your  ``__openerp__.py`` if needed.

This command is aware of any XML records already declared in
your module, and will update an existing declaration in-place.

Relations between object are followed if specified and import is then
cascaded.

The ``--help`` is complete (as all other commands). Here are
some specific example of use on various points.


specifying target database
""""""""""""""""""""""""""

You can specify the database through the command line::

   ## import in XML the user ``fabrice`` in database ``db_prod``

   $ oem rec import --db db_prod res.users --name fabrice

Please note that if you work with the same database for a while
you'lll probably want to save the default database to avoid specifying
it every time::

   $ oem db use db_prod
   $ oem rec import ir.ui.menu --id 356

This command will save in your ``~/.oem.rc`` the default db in the key
``default_db``. If you which to store this information in your module-local
config file you should add ``--local`` as follow::

    $ oem db use db_prod --local

If you wonder what is your current ``default_db``, you can ask without using any
argument::

    $ oem db use

It'll display the current value.


imported fields specification
"""""""""""""""""""""""""""""

Fields that gets imported in XML are configurable::

   ## import partner ``fabrice`` without the fields ``image``, ``ìmage_medium``, ``image_small``

   $ oem rec import res.partner --name fabrice --fields -image,-image_medium,-image_small

You can setup the default fields that get imported per model for
specific module, or globally with the config key
``rec.import.fields``.  This can be set or modified in your
``~/.oem.rc`` for global configuration (or ``.oem.rc`` in the root of
your module for local configuration).

Here's how to set the previous fields with ``oem config set``::

    oem config set rec.import.fields.'res\.partner' ,-image,-image_medium,-image_small

Notice 2 shell tricks/caveat when using command line ``oem config set``:

- the model name containes a dot, but ``oem config set`` uses dots to
  browse into sub-keys. So we need to escape the dot with a slash.
- second, to avoid having the final argument mistaken with a command
  line option (due to the leading ``-``), we artificially added a
  comma ``,`` in front of the list of fields.

The YAML config entry in the config file will look like this::

  rec:
    import:
      fields:
        res.partner: ',-image,-image_medium'

Note that by default, these are part of the default config file in your
module (installed by ``oem init`` and provided by the default template)::

  rec:
    import:
      fields:
        *: *,-create_uid,-write_uid,-create_date,-write_date,-__last_update
        ir.actions.act_window: name,type,res_model,view_id,view_type,view_mode,target,usage,domain,context

Note that:

- ``*`` as a model key stands for all models,
- ``*`` as a field name stand for all fields.
- You can use ``-`` in front of a field to remove it, and ``+`` (or
  nothing) to add it.

Please bear in mind that:

- You cannot remove a required field (import would fail anyway), it'll be ignored.
- You cannot add read-only field (import would fail anyway). it'll be ignored.
- You can add complex types as references, many2many, one2many, this will trigger
  cascading import.


On the command line, the format is
``[MODEL:]FIELD1[,FIELD2[,...]][;[MODEL2:]FIELD21[,FIELD22[,...]]]``,
as this might not be so clear, here are detailled explanations:

- fields are separated by ``,``, and use ``-`` or ``+`` in front of their name to remove
  or add them.
- use ``MODEL:`` in front of field list to specify their model, otherwise, the
  current model will be used. So::

    ## explicit field specification on the command line:

    $ oem rec import res.partner --fields res.partner:image,-image_medium

    ## in the following field specification, the model is not specified, so
    ## it'll be defaulted to current model being imported: ``res.partner``.

    $ oem rec import res.partner --fields image,-image_medium

- you can specify several fields specification for several models by
  using semicolon ``;`` for separating them. This can be useful when
  cascading through models thanks to one2many fields or any other
  complex field.

Command line values have priority over config file values. You should probably
store your field specification instead of using command line to avoid complexity.
Command line specification are nice for one-shot imports.


file dispatching
""""""""""""""""

Your records gets dispatched in files, but you can specify where you want them to be
created, thanks to ``--out`` option::

   ## import partner ``fabrice`` without the fields ``image``, ``ìmage_medium``, ``image_small``

   $ oem rec import res.partner --name fabrice --out personnel/fabrice.xml

Subdirectory will be created accordingly, and the new file will be
added in ``__openerp__.py``.  However, be warned that if your record
happen to already be stored in XML, it will be updated in place and
your ``--out XXX`` option won't be used. (this might change in the
future however)

Your records gets dispatched in files in your module according to a
dispatching specification. As usual, this can be set for one module or
globally through the ``.oem.rc`` files. The sub-key concerned is
``rec.import.dispatch``. Here's the default value from the the default
``.oem.rc`` file::

    rec:
      import:
        dispatch:
          '*': data/%(_model_underscore)s.xml
          ir.actions.act_url: actions/act_url.xml
          ir.actions.act_window: actions/act_window.xml
          ir.actions.actions: actions/action.xml
          ir.actions.client: actions/client.xml
          ir.actions.server: actions/server.xml
          ir.ui.menu: menu.xml
          ir.ui.views: views/view.xml

it's a ``MODEL: FILENAME`` dictionary. The ``*`` for model stands for
all models. The filename specifier can use python dictionary
interpolation keys as it'll be interpolated with a dict containing the
field, values of the current record to be dispatched with some
additional metadata information as:

- ``_model`` for the model of the current record.
- ``_model_underscore`` for the model of the current record with
  underscore inplace of dots.

So for instance to add a new dispatching place, you could use ``oem config set``::

    oem config set rec.import.dispatch.'res\.partner' "personnel/%(name).xml"



Contributing
============

Any suggestion or issue is welcome. Push request are very welcome,
please check out the guidelines.


Push Request Guidelines
-----------------------

You can send any code. I'll look at it and will integrate it myself in
the code base and leave you as the author. This process can take time and
it'll take less time if you follow the following guidelines:

- check your code with PEP8 or pylint. Try to stick to 80 columns wide.
- separate your commits per smallest concern.
- each commit should pass the tests (to allow easy bisect)
- each functionality/bugfix commit should contain the code, tests,
  and doc.
- prior minor commit with typographic or code cosmetic changes are
  very welcome. These should be tagged in their commit summary with
  ``!minor``.
- the commit message should follow gitchangelog rules (check the git
  log to get examples)
- if the commit fixes an issue or finished the implementation of a
  feature, please mention it in the summary.

If you have some questions about guidelines which is not answered here,
please check the current ``git log``, you might find previous commit that
would show you how to deal with your issue.


License
=======

Copyright (c) 2015 Valentin Lab.

Licensed under the `BSD License`_.

.. _BSD License: http://raw.github.com/0k/oem/master/LICENSE
