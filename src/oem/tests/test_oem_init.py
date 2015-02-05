# -*- encoding: utf-8 -*-

import os.path

from common import BaseTest
import kids.file as kf


class OemInitTest(BaseTest):

    COMMAND = 'init'

    def test_no_args(self):
        out, err, errlvl = self.cmd('$tprog')
        self.assertEqual(
            errlvl, 1,
            msg="Should fail because of missing author informations..")
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%s" % err)

    def test_no_args_but_git(self):

        print self.w("""

            git init . &&
            git config user.name "Robert Dubois" &&
            git config user.email "robert.dubois@mail.com"

        """)
        out, err, errlvl = self.cmd(
            "NO_GIT_CONFIG= "  ## enables GIT CONFIG
            "OEM_INIT_TEMPLATE=$BASE_PATH/tests/fixtures/fake-template "
            "$tprog ")
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed on simple directory and without args "
                 "(errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            kf.get_contents("LICENSE"), "Robert Dubois",
            msg="The author name should at least be in the LICENSE.")

    def test_with_args(self):
        out, err, errlvl = self.cmd(
            "OEM_INIT_TEMPLATE=$BASE_PATH/tests/fixtures/fake-template "
            "$tprog "
            "--author='Robert Dubois <robert.dubois@mail.com>'")
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed on simple directory and with args"
                 "(errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output displayed. "
            "Current stderr:\n%r" % err)

        self.assertTrue(os.path.exists('__openerp__.py'),
                        msg="At least file '__openerp__.py' should be created")

    def test_with_subdir(self):
        out, err, errlvl = self.cmd(
            "OEM_INIT_TEMPLATE=$BASE_PATH/tests/fixtures/fake-template "
            "$tprog subdir "
            "--author='Robert Dubois <robert.dubois@mail.com>' ")
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed on simple template and with subdir"
                 "(errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output displayed. "
            "Current stderr:\n%r" % err)
        self.assertTrue(os.path.exists('subdir/__openerp__.py'),
                        msg="At least file '__openerp__.py' should be created")
