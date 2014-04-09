import os
import unittest
import tempfile

from bork import buuk


class BuuksTest(unittest.TestCase):
    def test_buuks(self):
        return


PATH = "%s/../../buuks/.test" % os.path.dirname(__file__)


class PathTest(unittest.TestCase):
    def test_path(self):
        b = buuk.Path(PATH)
        self.assertTrue(os.path.isdir(b.path()))

    def test_ls(self):
        b = buuk.Path(PATH)
        got = b.ls('ls')
        got.sort()
        self.assertEqual(got, ['1', '2', '3'])

    def test_ls_full(self):
        b = buuk.Path(PATH)
        got = b.ls('ls', full=True)
        got.sort()

    def test_exists(self):
        b = buuk.Path(PATH)
        self.assertTrue(b.exists('ls'))
        self.assertFalse(b.exists('boris'))

    def test_content(self):
        b = buuk.Path(PATH)
        self.assertEqual(b.content('content'), 'foo')

    def test_template(self):
        # TODO
        return
        b = buuk.Path(PATH)
        self.assertEqual(b.template('foo.txt', {'name': 'tom'}), 'name: tom')

    def test_put(self):
        # TODO
        return
        tempfile_path = tempfile.mkstemp()[1]
        try:
            b = buuk.Path(PATH)
            want = "Mary had a little lamb.\n"
            b.put(want, tempfile_path, mode='0600')
            got = open(tempfile_path).read()
            self.assertEqual(got, want)
            self.assertEqual(os.stat(tempfile_path)[0], 33152)
        finally:
            os.remove(tempfile_path)

    def test_put_sudo(self):
        # don't want the test suite to pause for a password, so normally this
        # test won't run
        # TODO
        return
        return
        tempfile_path = tempfile.mkstemp()[1]
        try:
            b = buuk.Path(PATH)
            want = "Mary had a little lamb.\n"
            b.put(want, tempfile_path, sudo = True, mode='0777')
            got = open(tempfile_path).read()
            self.assertEqual(got, want)
            self.assertEqual(os.stat(tempfile_path)[0], 33279)
            self.assertEqual(os.stat(tempfile_path)[4], 0)
        finally:
            os.remove(tempfile_path)

    def test_put_template(self):
        # TODO
        return
        tempfile_path = tempfile.mkstemp()[1]
        try:
            b = buuk.Path(PATH)
            b.put_template('foo.txt', {'name': 'tom'}, tempfile_path)
            got = open(tempfile_path).read()
            self.assertEqual(got, 'name: tom')
        finally:
            os.remove(tempfile_path)
