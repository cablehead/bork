import os

from bork import config
from bork import shell


TEMPLATES_CONFIGURED = False


class Buuks(object):
    def __init__(self, paths):
        self.repos = [Repo(x) for x in paths]

    def paths(self, *a):
        return [x.Path(*a) for x in self.repos]

    def repo(self, name):
        return [x for x in self.repos if x.name == name][0]

    @property
    def amis(self):
        return Overlay(self.paths('amis'))

    @property
    def authorized_keys(self):
        return Overlay(self.paths(), method='cat')['authorized_keys']

    @property
    def domain(self):
        return Overlay(self.paths())['domain']

    @property
    def private_key(self):
        return Overlay(self.paths())['private_key']

    @property
    def boot(self):
        return Overlay(self.paths('boot'))

    @property
    def groups(self):
        return Overlay(self.paths('groups'), method='lines')

    def package(self, name):
        for path in self.paths('packages'):
            if path.exists(name):
                return Package(self, path.repo, path.path(name))


class Overlay(object):
    def __init__(self, paths, method='content'):
        self.paths = paths
        self.method = method

    def __getitem__(self, name):
        for path in self.paths:
            if path.exists(name):
                return getattr(path, self.method)(name)


class Path(object):
    def __init__(self, repo, path):
        self.repo = repo
        self._path = path

    def path(self, *a):
        return os.path.join(self._path, *a)

    def Path(self, *a):
        return Path(self.repo, self.path(*a))

    def ls(self, *a, **kw):
        if not self.exists(*a):
            return []
        ret = os.listdir(self.path(*a))
        if kw.get('full'):
            return [os.path.join(self.path(*a), x) for x in ret]
        return ret

    def exists(self, *a):
        return os.path.exists(self.path(*a))

    def content(self, *a):
        if not self.exists(*a):
            return ''
        return open(self.path(*a)).read().strip()

    def cat(self, *a):
        if not self.exists(*a):
            return ''
        ret = []
        for name in self.ls(*a):
            ret.append(self.Path(*a).content(name))
        return '\n'.join(ret)

    def lines(self, *a):
        return [
            x for x in self.content(*a).split('\n')
                if x and not x.startswith('#')]

    def template(self, name, context):
        # TODO: there's got to be something lighter we can use for templating?
        from django.template import Template, Context
        from django.conf import settings

        global TEMPLATES_CONFIGURED
        if not TEMPLATES_CONFIGURED:
            settings.configure(TEMPLATE_DIRS=("",))
            TEMPLATES_CONFIGURED = True

        if not self.exists('templates', name):
            raise Exception('Template not found: %s' % name)

        t = Template(self.content('templates', name))
        return t.render(Context(context))

    def put_template(self, name, context, dest, sudo=False, mode=None):
        self.put(self.template(name, context), dest, sudo=sudo, mode=mode)


class Repo(Path):
    def __init__(self, path):
        self.repo = self
        self._path = path
        self.name, ext = os.path.splitext(os.path.basename(self.origin()))

    def __repr__(self):
        return "<Repo: %s>" % self.name

    def branch(self):
        return shell.run("""
            cd %s
            git branch | sed -n '/\* /s///p'
            """ % self._path)[0].strip()

    def origin(self):
        return shell.run("""
            cd %s
            git remote show -n origin | grep Fetch | awk {'print $3'}
            """ % self._path)[0].strip()


class Package(Path):
    def __init__(self, buuks, repo, path):
        self.buuks = buuks
        self.repo = repo
        self._path = path
        self.name = os.path.basename(path)

    @property
    def role(self):
        return self.content('role')

    def groups(self):
        ret = set(['base'])
        for package in self.chain():
            ret |= set(self.buuks.package(package).lines('groups'))
        ret |= set(self.lines('groups'))
        return list(ret)

    def chain(self):
        # dependency chain
        ret = []
        for package in self.lines('packages'):
            sub_packages = self.buuks.package(package).chain()
            for p in sub_packages + [package]:
                if p not in ret:
                    ret.append(p)
        return ret

    def repos(self):
        ret = [self.buuks.repo('bork')]
        for name in self.chain() + [self.name]:
            repo = self.buuks.package(name).repo
            if repo not in ret:
                ret.append(repo)
        return ret

    def install_root_service(self, name):
        path = self.path('sv', name)
        shell.sudo('ln -s %s /etc/service' % path)

    def _install_bash(self):
        for script in self.ls('bash'):
            shell.run(self.content('bash', script))

    def _install_overlay(self):
        if self.exists('overlay'):
            shell.sudo('rsync -avzp . /', cwd=self.path('overlay'))

    def _install_debconf(self):
        for selfile in self.ls('debconf'):
            shell.sudo(
                'debconf-set-selections < %s' % self.path('debconf', selfile))

    def _install_ppa(self):
        ppas = self.ls('ppa')
        if ppas:
            for ppa_name in ppas:
                ppa_label = open('%s/%s' % ( self.path('ppa'), ppa_name ) ).read()
                shell.sudo('add-apt-repository %s' % ppa_label)

    def _install_apt(self):
        shell.sudo('apt-get update')
        apts = self.ls('apt')
        if apts:
            shell.sudo(
                'DEBIAN_FRONTEND=noninteractive apt-get -qq -o Dpkg::Options::="--force-confold" install %s' %
                    ' '.join(apts))

    def _install_debs(self):
        debs = self.ls('debs', full=True)
        if debs:
            shell.sudo('dpkg -i %s' % ' '.join(debs))

    def _install_pip(self):
        if self.exists('pip'):
            shell.sudo(
                'pip install -r %s' % self.path('pip'))

    def _install_git(self):
        for repo in self.lines('git'):
            shell.run('cd ~/git && git clone --recursive %s' % repo)

    def _install_users(self):
        for user in self.ls('users'):
            shell.sudo(
                'adduser --system --no-create-home --group %s' % user)

    def _install_env(self):
        shell.run('mkdir -p ~/env')
        for path in ['all', config.aws.env]:
            if self.exists('env', path):
                shell.run('cp %s ~/env' % self.path('env', path, '*'))

    def _install_sv(self):
        shell.run('mkdir -p ~/sv')
        for path in self.ls('sv', full=True):
            name = os.path.basename(path)
            shell.run('mkdir -p ~/sv/%s' % name)

            # if the sv template is a directory, link all of the files in the
            # directory to ~/sv/<name>, otherwise, if it's a single file, link
            # that file as run to ~/sv/<name>
            if os.path.isdir(path):
                for file_ in self.ls('sv', name, full=True):
                    shell.run('ln -sf %s ~/sv/%s' % (file_, name))

            else:
                shell.run('ln -sf %s ~/sv/%s/run' % (path, name))

            # link env for all sv templates
            shell.run('ln -sf ~/env ~/sv/%s/env' % name)

            shell.run('mkdir -p ~/sv/%s/log' % name)
            shell.put(
                '#!/bin/sh\nset -e\nexec svlogd -tt ./\n',
                '~/sv/%s/log/run' % name,
                mode='0755')

    def _install_sv_root(self):
        for path in self.ls('sv.root', full=True):
            shell.sudo('ln -s %s /etc/service' % path)

    def _install_gems(self):
        for gem in self.lines('gems'):
            shell.run('sudo gem install %s' % gem)

    def _install_circus(self):
        shell.run('mkdir -p ~/service/msgme-circus/ini')
        shell.run(
            'ln -s %s/* ~/service/msgme-circus/ini' % self.path('circus'))
        shell.run('sv restart ~/service/msgme-circus')

    def install(self, dependencies=False):
        """
        - if dependencies is '', just this package will be installed
        - if dependencies is 'all', all of this package's dependency chain will
          be installed, and then this package will be installed
        - if dependencies is a string, it's assumed to be the package name of
          all dependencies already met, including possibly this current
          package; in which case all packages after the met dependency will be
          installed
        """
        if dependencies:
            if dependencies == self.name:
                # all dependencies satisfied, no more to do
                return

            # install from the met dependency on
            chain = self.chain()
            if dependencies in chain:
                chain = chain[chain.index(dependencies)+1:]

            for package in chain:
                p = self.buuks.package(package)
                p.install()

        if os.path.isfile(self.path()):
            # simple text file, run as a bash snippet
            shell.run(self.content())
            return

        for goo in [
                'bash', 'overlay', 'debconf', 'ppa', 'apt', 'debs', 'git',
                'gems', 'users', 'env', 'circus']:
            if self.exists(goo):
                getattr(self, '_install_%s' % goo)()

        if self.exists('install.py'):
            e = {}
            execfile(self.path('install.py'), e)
            e['install'](self)

        self._install_pip()
        self._install_sv()
        self._install_sv_root()
