from fabric.colors import green, red
from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import sudo
from fabric.tasks import execute
from fabric.utils import puts, abort
from fabtools import require

__all__ = ['bootstrap_cluster', 'install', 'setup_peering', 'config_volume', 'info', 'status']

default_volume_name = 'gv0'
storage_path = '/gluster-storage'


@task
def bootstrap_cluster(host_a, host_b, host_c, volume_name=None):
    """Creates a simple replicated volume with `len(hosts)` replicas."""
    puts(red("Gluster uses the reverse DNS of each peer hostname to authenticate it."))
    msg = 'Have you made sure the reverse DNS for each node has properly resolved?'
    can_continue = confirm(msg, default=False)
    if not can_continue:
        abort('do your dns work now')

    def do_node(host):
        puts(green('Installing GlusterFS on {}'.format(host)), flush=True)
        execute(install, host=host)

    if volume_name is None:
        volume_name = default_volume_name

    do_node(host_a)
    do_node(host_b)
    do_node(host_c)
    execute(setup_peering, [host_b, host_c], host=host_a)
    execute(config_volume, volume_name, [host_a, host_b, host_c], host=host_a)


@task
def install():
    """Install required GlusterFS software and extras."""
    require.deb.package('software-properties-common')
    # Gluster 3.9+ is not available on Ubuntu 14.04
    require.deb.ppa('ppa:gluster/glusterfs-3.8')
    require.deb.package('glusterfs-server')
    require.deb.ppa('ppa:gluster/glusterfs-coreutils')
    require.deb.package('glusterfs-coreutils')


@task
def setup_peering(peer_hosts):
    """Make sure you do this only on *ONE* host."""
    for host in peer_hosts:
        sudo('gluster peer probe {}'.format(host))


@task
def config_volume(volume_name, hosts):
    """Make sure you do this only on *ONE* host."""
    replica_num = len(hosts)
    cmd_prefix = 'gluster volume create {} replica {} transport tcp'.format(
        volume_name, replica_num)

    host_volume_args = []
    for host in hosts:
        arg = '{}:{}'.format(host, storage_path)
        host_volume_args.append(arg)

    sudo("{} {} force".format(cmd_prefix, " ".join(host_volume_args)))

    sudo('gluster volume start {}'.format(volume_name))


@task
def info():
    sudo('gluster volume info')


@task
def status():
    sudo('gluster peer status')
