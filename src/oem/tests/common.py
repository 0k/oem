# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os

import kids.test
from kids.sh import sh
from kids.cache import cache


def set_env(**se_kwargs):

    def decorator(f):

        def _wrapped(*args, **kwargs):
            kwargs["env"] = dict(kwargs.get("env") or os.environ)
            for key, value in se_kwargs.items():
                if key not in kwargs["env"]:
                    kwargs["env"][key] = value
            return f(*args, **kwargs)
        return _wrapped
    return decorator


BASE_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    ".."))
tprog = os.path.join(BASE_PATH, "oem.py")

WITH_COVERAGE = sh.cmd("type coverage")[2] == 0
if WITH_COVERAGE:
    tprog_set = set_env(
        BASE_PATH=BASE_PATH,
        COVERAGE_FILE="%s/.coverage.2" % BASE_PATH,
        PYTHONPATH="%s" % BASE_PATH,
        tprog=('coverage run -a --source=%(base_path)s '
               '--omit=%(base_path)s/setup.py'
                   # '%(base_path)s/gitchangelog.rc* '
               '--rcfile="%(base_path)s/.coveragerc" %(tprog)s'
               % {'base_path': BASE_PATH,
                  'tprog': tprog}))
else:
    tprog_set = set_env(
        BASE_PATH=BASE_PATH,
        tprog=tprog
    )

w = tprog_set(sh.wrap)
cmd = tprog_set(sh.cmd)


class BaseTest(kids.sh.BaseShTest, kids.test.BaseTmpDirTest):

    COMMAND = ""

    @cache
    @property
    def DEFAULT_ENV(self):
        return {
            'tprog': (("%s %s" % (tprog, self.COMMAND))
                      if self.COMMAND else tprog),
            'BASE_PATH': BASE_PATH,
            'NO_GIT_CONFIG': "true"
        }

    def test_simple_run(self):
        out, err, errlvl = self.cmd('$tprog --help')
        self.assertEqual(
            errlvl, 0,
            msg=("Should not fail on simple --help (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no stderr outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "Usage:",
            msg="Usage info should be at least be displayed in stdout... "
            "Current stdout:\n%s" % out)
