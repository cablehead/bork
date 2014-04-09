import unittest

from bork import shell

class ShellTest(unittest.TestCase):
    def test_run(self):
        out, err = shell.run('echo hi')
        self.assertEqual(out, 'hi\n')
        self.assertEqual(err, '')

    def test_run_with_stdin(self):
        out, err = shell.run('cat', stdin='hi')
        self.assertEqual(out, 'hi')
        self.assertEqual(err, '')

    def test_sudo(self):
        # don't want the test suite to pause for a password, so normally this
        # test won't run
        return
        out, err = shell.sudo('whoami')
        self.assertEqual(out, 'root\n')

    def test_run_multiline(self):
        out, err = shell.run('echo hi\necho foo | grep -v foo\necho hi again')
        self.assertEqual(out, 'hi\nhi again\n')
        self.assertEqual(err, '')
