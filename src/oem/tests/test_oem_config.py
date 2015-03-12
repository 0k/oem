# -*- encoding: utf-8 -*-

import os
import os.path

from .common import BaseTest
import kids.file as kf


class OemConfigTest(BaseTest):

    COMMAND = 'config'

    def test_get_empty(self):
        out, err, errlvl = self.cmd(
            '$tprog get')
        self.assertEqual(
            errlvl, 0,
            msg=("should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            out, "",
            msg="Should display empty config. "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            err, "",
            msg="Should not output anything on stderr. "
            "Current stderr:\n%s" % err)
        self.assertTrue(
            all(not kf.chk.exists(f)
                for f in self.cfg_files))

    def test_global_get_empty(self):
        out, err, errlvl = self.cmd(
            '$tprog get --global')
        self.assertEqual(
            errlvl, 0,
            msg=("should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            out, "",
            msg="Should display empty config. "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            err, "",
            msg="Should not output anything on stderr. "
            "Current stderr:\n%s" % err)
        self.assertTrue(
            all(not kf.chk.exists(f)
                for f in [self.system_filename,
                          self.global_filename]))

    def test_set(self):
        out, err, errlvl = self.cmd(
            '$tprog set a.b.c.d 2')
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            out, "",
            msg="Should not display anything on stdout. "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            err, "",
            msg="Should not display anything on stderr. "
            "Current stderr:\n%s" % err)

    def test_global_set(self):
        out, err, errlvl = self.cmd(
            '$tprog set --global a.b.c.d 2')
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            out, "",
            msg="Should not display anything on stdout. "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            err, "",
            msg="Should not display anything on stderr. "
            "Current stderr:\n%s" % err)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))


class NoLocalPathOemConfigTest(OemConfigTest):

    def test_local_get_empty(self):
        out, err, errlvl = self.cmd(
            '$tprog get --local')
        self.assertNotEqual(
            errlvl, 0,
            msg="Should fail.")
        self.assertEqual(
            out, "",
            msg="Should not display anything on stdout. "
            "Current stdout:\n%s" % out)
        self.assertContains(
            err, "local",
            msg="Should output an error message containing 'local' on stderr. "
            "Current stderr:\n%s" % err)
        self.assertTrue(
            all(not kf.chk.exists(f)
                for f in [self.system_filename,
                          self.global_filename]))

    def test_set(self):
        super(NoLocalPathOemConfigTest, self).test_set()
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))

    def test_local_set(self):
        out, err, errlvl = self.cmd(
            '$tprog set --local a.b.c.d 2')
        self.assertNotEqual(
            errlvl, 0,
            msg=("Should fail. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            out, "",
            msg="Should not display anything on stdout. "
            "Current stdout:\n%s" % out)
        self.assertContains(
            err, "local",
            msg="Should output an error message containing 'local' on stderr. "
            "Current stderr:\n%s" % err)
        self.assertTrue(
            all(not kf.chk.exists(f)
                for f in [self.system_filename,
                          self.global_filename]))

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
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))


class LocalPathOemConfigTest(OemConfigTest):

    def setUp(self):
        super(LocalPathOemConfigTest, self).setUp()
        kf.mkdir("myaddon")
        os.chdir("myaddon")
        kf.touch("__openerp__.py")
        self.local_filename = os.path.join(self.tmpdir, "myaddon", ".oem.rc")
        self.cfg_files.append(self.local_filename)

    def test_local_get_empty(self):
        out, err, errlvl = self.cmd(
            '$tprog get')
        self.assertEqual(
            errlvl, 0,
            msg="Should succeed.")
        self.assertEqual(
            out, "",
            msg="Should display empty config. "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            err, "",
            msg="Should not output anything on stderr. "
            "Current stderr:\n%s" % err)
        self.assertTrue(
            all(not kf.chk.exists(f)
                for f in self.cfg_files))

    def test_global_set(self):
        super(LocalPathOemConfigTest, self).test_global_set()
        self.assertFalse(kf.chk.exists(self.local_filename))

    def test_local_set(self):
        out, err, errlvl = self.cmd(
            '$tprog set --local a.b.c.d 2')
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            out, "",
            msg="Should not display anything on stdout. "
            "Current stdout:\n%s" % out)
        self.assertEqual(
            err, "",
            msg="Should not display anything on stderr. "
            "Current stderr:\n%s" % err)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertFalse(kf.chk.exists(self.global_filename))
        self.assertTrue(kf.chk.exists(self.local_filename))

    def test_rm_get(self):
        out = self.w('$tprog set a.b.c.d 2')
        self.assertEqual(
            out, "",
            msg="Should display nothing. "
            "Current stdout:\n%s" % out)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertFalse(kf.chk.exists(self.global_filename))
        self.assertTrue(kf.chk.exists(self.local_filename))
        out = self.w('$tprog set --global a.x 3')
        self.assertEqual(
            out, "",
            msg="Should display nothing. "
            "Current stdout:\n%s" % out)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))
        self.assertTrue(kf.chk.exists(self.local_filename))
        out = self.w('$tprog set --global a.y 3 && $tprog set a.y 3')
        self.assertEqual(
            out, "",
            msg="Should display nothing. "
            "Current stdout:\n%s" % out)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))
        self.assertTrue(kf.chk.exists(self.local_filename))
        out, err, errlvl = self.cmd(
            '$tprog rm a.b.c.d')
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard output outputed. "
            "Current stdout:\n%r" % out)
        self.assertEqual(
            out, "",
            msg="There should be no standard error displayed. "
            "Current stderr:\n%r" % err)
        out = self.w('$tprog get a.b.c.d', ignore_errlvls=[1])
        self.assertEqual(
            out, "",
            msg="Should not display anything. "
            "Current stdout:\n%s" % out)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))
        self.assertTrue(kf.chk.exists(self.local_filename))

        out, err, errlvl = self.cmd(
            '$tprog rm a.x')
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard output outputed. "
            "Current stdout:\n%r" % out)
        self.assertEqual(
            out, "",
            msg="There should be no standard error displayed. "
            "Current stderr:\n%r" % err)
        out = self.w('$tprog get a.x', ignore_errlvls=[1])
        self.assertEqual(
            out, "",
            msg="Should not display anything. "
            "Current stdout:\n%s" % out)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))
        self.assertTrue(kf.chk.exists(self.local_filename))

        out, err, errlvl = self.cmd(
            '$tprog rm a.y')
        self.assertEqual(
            errlvl, 0,
            msg=("Should succeed. (errlvl=%r)\n%s"
                 % (errlvl, err)))
        self.assertEqual(
            err, "",
            msg="There should be no standard output outputed. "
            "Current stdout:\n%r" % out)
        self.assertEqual(
            out, "",
            msg="There should be no standard error displayed. "
            "Current stderr:\n%r" % err)
        out = self.w('$tprog get a.y', ignore_errlvls=[0])
        self.assertEqual(
            out, "3",
            msg="Should be displaying 3. "
            "Current stdout:\n%s" % out)
        self.assertFalse(kf.chk.exists(self.system_filename))
        self.assertTrue(kf.chk.exists(self.global_filename))
        self.assertTrue(kf.chk.exists(self.local_filename))
