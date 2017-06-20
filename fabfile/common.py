from fabric.contrib.files import sed
from fabric.decorators import task
from fabric.operations import run
from fabtools import deb, require, service

from . import files

__all__ = ['dist_upgrade', 'set_hostname']


@task
def dist_upgrade():
    deb.update_index(quiet=True)
    deb.upgrade(safe=False)


def install_fail2ban():
    require.deb.package(['fail2ban'])
    if not service.is_running('fail2ban'):
        service.start('fail2ban')


@task
def set_hostname(short_hostname):
    require.file(files.remote.hostname, contents="{hostname}\n".format(hostname=short_hostname))
    sed(files.remote.hosts, '(\s*127\.0\.1\.1\s+)\w+$', '\\1{hostname}'.format(hostname=short_hostname))
    run('hostname {hostname}'.format(hostname=short_hostname))
