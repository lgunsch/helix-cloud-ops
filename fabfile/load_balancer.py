import re

from fabric.contrib.files import sed
from fabric.decorators import task
from fabric.operations import put
from fabric.tasks import execute
from fabric.utils import abort

from fabtools import require, service, deb

from . import files
from .common import install_fail2ban, set_hostname

__all__ = ['setup']


@task
def setup(short_hostname):
    deb.update_index()

    install_fail2ban()

    # HAProxy determines it's local name from hostname, and expects it
    # to have a "peer lb-1 ld-1.helix-cloud.ca" section present.
    # Thanks to the Debian HAProxy packaging team!
    with open(files.haproxy_cfg) as fp:
        cfg = fp.read()
        if not re.search(r'^\s*peer\s+{}'.format(short_hostname), cfg,
                         flags=re.MULTILINE):
            abort("hostname does not match any set in HAProxy config!")

    execute(set_hostname, short_hostname)

    # Newer versions of HAProxy support "peers", which is good
    require.deb.package('software-properties-common')
    require.deb.ppa('ppa:vbernat/haproxy-1.7')
    require.deb.package('haproxy')

    # no such thing as \d in sed regex
    sed('/etc/default/haproxy', 'ENABLED=[[:digit:]]', 'ENABLED=1')
    put(files.haproxy_cfg, '/etc/haproxy/haproxy.cfg')
    service.restart('haproxy')
