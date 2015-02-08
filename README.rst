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

For now, because we use specific ``cookiecutter`` and ``ooop`` versions,
you should install it from source::

    pip install -r requirements.txt
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

TBD


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
