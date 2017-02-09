from getpass import getpass

from fabric.colors import red
from fabric.contrib.files import upload_template
from fabric.decorators import task
from fabric.operations import run, put
from fabric.utils import puts, abort
from fabtools import require, service

from . import templates, files

__all__ = ['install', 'install_arbitrator', 'bootstrap_cluster', 'start',
           'add_node', 'add_admin']


@task
def install(wresp_cluster_address):
    """Install MariaDB Galera Cluster.
    :param wresp_cluster_address: See https://mariadb.com/kb/en/mariadb/galera-cluster-system-variables/#wsrep_cluster_address
    """
    require.deb.package('software-properties-common')
    require.deb.add_apt_key(keyid='0xcbcb082a1bb943db',
                            keyserver='hkp://keyserver.ubuntu.com:80',
                            update=False)  # we'll update after adding the repo
    run("add-apt-repository 'deb [arch=amd64,i386,ppc64el] http://mariadb.mirror.anstey.ca/repo/10.1/ubuntu trusty main'")
    require.deb.update_index(quiet=True)

    # Use `fabtools.deb.preseed_package` to have un-attended password
    # creation with `deb.install`, but for now we'll just type it in.
    # require.deb.install(['mariadb-server'])
    run('apt-get install mariadb-server')

    put(files.galera_provider, '/var/tmp/')
    run('dpkg --install /var/tmp/{}'.format(files.galera_provider.name))
    upload_template(str(templates.my_cnf.name),
                    '/etc/mysql/my.cnf',
                    use_jinja=True,
                    template_dir=templates.dir,
                    context={'wresp_cluster_address': wresp_cluster_address})


@task()
def install_arbitrator():
    pass


@task
def bootstrap_cluster():
    """Run on the first machine of a new cluster, without any mysqld daemons running."""
    puts(red('This should be run on the FIRST machine of the new cluster'))
    puts(red('No other mysqld daemons should be running for this cluster'))
    run('service mysql bootstrap')


@task
def start():
    """Run after bootstrapping the first node of the cluster."""
    if service.is_running('mysql'):
        puts(red('MariaDB is already running. Reloading instead.'))
        service.reload('mysql')
    else:
        service.start('mysql')


@task
def add_node(existing_member_hostname):
    """Given a bootstrapped Galera cluster, add/reconnect this node using another running node IP/hostname."""
    url = "gcomm://{}".format(existing_member_hostname)
    puts('Connecting using existing cluster member {}'.format(url))
    run('mysqld --wsrep_cluster_address={}'.format(url))


@task
def add_admin(username):
    """Add an admin user, for normal users connect with `mysql-workbench`."""
    if username.strip() in ['root', 'admin', 'helix-cloud']:
        abort("Do not make the username so predictable!")

    # check if user exists to avoid cryptic SQL errors below
    run('! mysql -D mysql -e "SELECT USER FROM mysql.user" | grep {}'
        .format(username))
    password = getpass("Password for {}:".format(username))

    # easier to debug with lines printed, even though the password is visible
    # also don't use `r` raw strings, otherwise the \ escapes will be passed through
    run("mysql -D mysql -e \"CREATE USER '{}'@'%' IDENTIFIED BY '{}'\""
        .format(username, password), pty=True)
    run("mysql -D mysql -e \"GRANT ALL PRIVILEGES ON *.* TO '{}'@'%' WITH GRANT OPTION\""
        .format(username, password), pty=True)
    run("mysql -D mysql -e \"FLUSH PRIVILEGES\"")
