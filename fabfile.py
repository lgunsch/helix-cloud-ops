import os
from contextlib import contextmanager

from fabric.api import local, sudo
from fabric.context_managers import cd
from fabric.decorators import task
from fabtools.vagrant import vagrant_settings
from fabtools import require


project = 'helix-cloud.ca'
repo = 'gitolite@helix-cloud.ca:helix-cloud.ca'
branch = 'master'

dh_virtualenv_reqs = [
    'debhelper',
    'python-dev',
    'build-essential',
    'devscripts',
    'dh-virtualenv',
]

# This is also contained in, and must be maintained in, debian/control
project_package_reqs = [
    'libpq-dev',
    'libfreetype6-dev',
    'libjpeg8-dev',
    'liblcms2-dev',
    'libsane-dev',
    'libwebp-dev',
    'zlib1g-dev',
    'git',
    'npm',
    'nodejs-legacy',  # don't even try the sym link nodejs to node funny business
]


@contextmanager
def build_box():
    local('vagrant destroy -f')
    local('vagrant up')

    with vagrant_settings():
        require.deb.ppa('ppa:spotify-jyrki/dh-virtualenv', auto_accept=True)
        require.deb.package(dh_virtualenv_reqs)
        require.deb.packages(project_package_reqs)

        ssh_config = """
            StrictHostKeyChecking no
            Host *.helix-cloud.ca
              Port 2022
            Host helix-cloud.ca
              Port 2022
        """
        require.directory('~/.ssh', mode='700')
        require.file('~/.ssh/config', contents=ssh_config)

        gitconfig = os.path.expanduser('~/.gitconfig')
        if os.path.exists(gitconfig):
            require.file('~/.gitconfig', source=gitconfig)

        require.git.working_copy(repo, branch=branch, path=project)

        # FIXME: return a "buildbox" object, as would be normally expected
        # It may contain a checkout_dir property or something
        yield project

    local('vagrant destroy -f')


@task
def changelog():
    with build_box():
        local('vagrant ssh')


@task
def buildpackage():
    with build_box() as project_dir:
        with cd(project_dir):
            sudo('dpkg-buildpackage -us -uc -b')
            # TODO: copy down built package here
