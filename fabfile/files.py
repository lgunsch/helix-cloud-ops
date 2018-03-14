from unipath import Path

__all__ = []


galera_provider = Path('./files/galera-3_25.3.23+1trusty_amd64.deb')
galera_arbitrator = Path('./files/galera-arbitrator-3_25.3.23+1trusty_amd64.deb')
haproxy_cfg = Path('./files/haproxy.cfg')


class remote:
    """Common OS file paths on remote systems."""
    hostname = '/etc/hostname'
    hosts = '/etc/hosts'
