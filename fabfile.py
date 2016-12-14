import os
from contextlib import contextmanager

from fabric.api import local, sudo
from fabric.colors import red
from fabric.context_managers import cd
from fabric.decorators import task
from fabric.operations import get
from fabric.utils import puts
from fabtools.vagrant import vagrant_settings
from fabtools import require


class Requirements(object):
    dh_virtualenv = [
        'debhelper',
        'python-dev',
        'build-essential',
        'devscripts',
        'dh-virtualenv',
    ]

    # This is also contained in, and must be maintained in, `debian/control`
    project_package = [
        'libpq-dev',
        'libfreetype6-dev',
        'libjpeg8-dev',
        'liblcms2-dev',
        'libsane-dev',
        'libwebp-dev',
        'zlib1g-dev',
        'git',
        'npm',
        'nodejs-legacy',  # avoid the sym link nodejs to node funny business
    ]


class Settings(object):
    project = 'helix-cloud.ca'
    repo = 'gitolite@helix-cloud.ca:helix-cloud.ca'
    branch = 'master'
    pkg_name = 'helix-cloud-ca'  # also maintained in `debian/control`
    ssh_config = """
        StrictHostKeyChecking no
        Host *.helix-cloud.ca
          Port 2022
        Host helix-cloud.ca
          Port 2022
    """


@task
def changelog(branch=None):
    settings = Settings()
    if branch is not None:
        puts('Using branch {}'.format(branch))
        settings.branch = branch

    with build_box(Requirements(), settings):
        local('vagrant ssh')


@task
def buildpackage(branch=None):
    settings = Settings()
    if branch is not None:
        puts('Using branch {}'.format(branch))
        settings.branch = branch

    puts(red("Don't forget to run `fab changelog` before this to create a "
             "new release version."))

    if not os.path.exists('build'):
        local('mkdir build')

    with build_box(Requirements(), settings) as env:
        with cd(env.clone_dir):
            sudo('dpkg-buildpackage -us -uc -b')
            get('/home/vagrant/{}*.deb'.format(settings.pkg_name),
                local_path='build/%(path)s')


class BuildBoxEnv(object):

    def __init__(self, clone_dir):
        self._clone_dir = clone_dir

    @property
    def clone_dir(self):
        return self._clone_dir


@contextmanager
def build_box(requirements, settings):
    """
    Args:
        requirements (Requirements):
        settings (Settings):

    Yields:
        BuildBoxEnv:
    """
    local('vagrant destroy -f')
    local('vagrant up')

    with vagrant_settings():
        require.deb.ppa('ppa:spotify-jyrki/dh-virtualenv', auto_accept=True)
        require.deb.package(requirements.dh_virtualenv)
        require.deb.packages(requirements.project_package)

        require.directory('~/.ssh', mode='700')
        require.file('~/.ssh/config', contents=settings.ssh_config)

        gitconfig = os.path.expanduser('~/.gitconfig')
        if os.path.exists(gitconfig):
            require.file('~/.gitconfig', source=gitconfig)

        require.git.working_copy(settings.repo, branch=settings.branch,
                                 path=settings.project)

        yield BuildBoxEnv(Settings.project)

    local('vagrant destroy -f')
