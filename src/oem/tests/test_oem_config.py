# -*- encoding: utf-8 -*-

import os
import os.path

from common import BaseTest
import kids.file as kf
from kids.data import dct
from kids.cache import cache


class OemConfigTest(BaseTest):

    COMMAND = 'config'

    @cache(key=lambda s: os.getcwd())
    @property
    def DEFAULT_ENV(self):
        env = super(OemConfigTest, self).DEFAULT_ENV
        return dct.merge(env, {
            'OEM_CONFIG_FILE': '%s/.oem.rc' % os.getcwd(),
        })

    def test_get_empty(self):
        out, err, errlvl = self.cmd(
            '$tprog get')
        self.assertEqual(
            errlvl, 0,
            msg="Should always succeed.")
        self.assertEqual(
            out, "",
            msg="Should display empty config. "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            err, "",
            msg="Should not output anything on stderr. "
            "Current stderr:\n%s" % err)

    def test_set_get(self):
        out, err, errlvl = self.cmd(
            '$tprog set a.b.c.d 2')
        self.assertEqual(
            errlvl, 0,
            msg=("Set should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stdout:\n%r" % out)
        self.assertEqual(
            out, "",
            msg="There should be no standard output displayed. "
            "Current stderr:\n%r" % err)

    def test_rm_get(self):
        out = self.w('$tprog set a.b.c.d 2')
        self.assertEqual(
            out, "",
            msg="Should display nothing. "
            "Current stdout:\n%s" % out)
        out, err, errlvl = self.cmd(
            '$tprog rm a.b.c.d')
        self.assertEqual(
            errlvl, 0,
            msg=("Set should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard output outputed. "
            "Current stdout:\n%r" % out)
        self.assertEqual(
            out, "",
            msg="There should be no standard error displayed. "
            "Current stderr:\n%r" % err)
        out = self.w('$tprog get')
        self.assertEqual(
            out, "",
            msg="Should display empty config. "
            "Current stdout:\n%s" % out)
