import logging
import subprocess

log = logging.getLogger(__name__)

def run(command, stdin=None, cwd=None):
    log.info('running: %s' % command)
    p = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd)
    stdout, stderr = p.communicate(stdin)
    if stdout:
        log.info(stdout)
    if stderr:
        log.error(stderr)
    return stdout, stderr


def sudo(command, stdin=None, cwd=None):
    return run('sudo su root -c "%s"' % command.replace('"', '\\"'), stdin=stdin, cwd=cwd)


def remote(host, command, trust=False):
    base = "export PYTHONPATH=~/git/borkbork:~/git/msgme-api"
    base += " && export PATH=$PATH:~/git/borkbork/bin"
    return run('ssh %subuntu@%s "%s && %s"' % (
        trust and '-o StrictHostKeychecking=no ' or '', host, base, command))


def put(data, dest, sudo=False, mode=None):
    if sudo:
        sh = sudo
    else:
        sh = run
    sh('cat > %s' % dest, stdin=data)
    if sudo:
        sh('chown root %s' % dest)
    if mode != None:
        sh('chmod %s %s' % (mode, dest))
