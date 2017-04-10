from getpass import getpass

from fabric.api import execute, task
from fabric.colors import red, green
from fabric.contrib.files import upload_template
from fabric.operations import run, put
from fabric.utils import puts, abort
from fabtools import require, service, deb

from . import templates, files

__all__ = ['build_cluster', 'install', 'install_arbitrator', 'bootstrap_cluster', 'start',
           'add_node', 'add_admin']

default_cluster_name = 'helix_cloud'


@task
def build_cluster(host_a, host_b, host_c, cluster_name=None):
    password = getpass('Root password for MariaDB (saved in ~/.my.cnf):')

    def note(msg): puts(green(msg), flush=True)

    def do_node(addr, peer_a, peer_b):
        note('Installing MariaDB on {}'.format(addr))
        galera_nodes = '{},{}'.format(peer_a, peer_b)
        execute(install, galera_nodes, cluster_name=cluster_name,
                password=password, host=addr)

    do_node(host_a, host_b, host_c)
    do_node(host_b, host_a, host_c)
    do_node(host_c, host_a, host_b)

    execute(bootstrap_cluster, host=host_a)
    execute(start, host=host_b)
    execute(start, host=host_c)


@task
def install(galera_nodes, cluster_name=None, password=None):
    """Install MariaDB Galera Cluster.

    :param galera_nodes: Do not include `gcomm://` prefix;
        See http://galeracluster.com/documentation-webpages/mysqlwsrepoptions.html#wsrep-cluster-address
    """
    if cluster_name is None:
        cluster_name = default_cluster_name

    install_fail2ban()

    require.deb.package('software-properties-common')
    require.deb.add_apt_key(keyid='0xcbcb082a1bb943db',
                            keyserver='hkp://keyserver.ubuntu.com:80',
                            update=False)  # we'll update after adding the repo
    run("add-apt-repository 'deb [arch=amd64,i386,ppc64el] http://mariadb.mirror.anstey.ca/repo/10.1/ubuntu trusty main'")
    require.deb.update_index(quiet=True)

    if password is None:
        password = getpass("Root password for mariadb (saved in ~/.my.cnf):")
    deb.preseed_package('mariadb-server', {
        'mysql-server/root_password': ('password', password),  # must be mysql, not mariadb here
        'mysql-server/root_password_again': ('password', password),
    })
    require.deb.install(['mariadb-server', 'galera-3'])

    put(files.galera_provider, '/var/tmp/')
    run('dpkg --install /var/tmp/{}'.format(files.galera_provider.name))
    upload_template(str(templates.my_cnf.name),
                    '/etc/mysql/my.cnf',
                    use_jinja=True,
                    template_dir=templates.dir,
                    context={'galera_nodes': galera_nodes,
                             'cluster_name': cluster_name})

    require.file('.my.cnf', mode="600", contents=(
        "[client]\n"
        "user=root\n"
        "password={}\n"
    ).format(password))


@task()
def install_arbitrator(galera_nodes, cluster_name=None):
    """Galera nodes must have port if arbitrator is running on same machine.

    :param galera_nodes: Do not include `gcomm://` prefix;
        See http://galeracluster.com/documentation-webpages/arbitrator.html
    """
    if cluster_name is None:
        cluster_name = default_cluster_name

    install_fail2ban()

    require.deb.install(['libboost-program-options1.54.0'])
    put(files.galera_arbitrator, '/var/tmp')
    run('dpkg --install /var/tmp/{}'.format(files.galera_arbitrator.name))
    upload_template(str(templates.arbitrator_config.name),
                    '/etc/default/garb',
                    use_jinja=True,
                    template_dir=templates.dir,
                    context={'galera_nodes': galera_nodes,
                             'cluster_name': cluster_name})


@task
def bootstrap_cluster():
    """Run on the first machine of a new cluster, without any mysqld daemons running."""
    puts(red('This should be run on the FIRST machine of the new cluster'))
    puts(red('No other mysqld daemons should be running for this cluster'))
    if service.is_running('mysql'):
        service.stop('mysql')
    # nohup below is very important. See:
    # http://serverfault.com/questions/709223/galera-new-cluster-wsrep-unknown-error-141
    run('nohup service mysql bootstrap')


@task
def start(name='mysql'):
    """Defaults to `mysql`, but may also be `garb` for the arbitrator."""
    # nohup below is very important. See:
    # http://serverfault.com/questions/709223/galera-new-cluster-wsrep-unknown-error-141
    if service.is_running(name):
        puts(red('{} is already running. Restarting (not reload) to '
                 'init cluster membership.'.format(name)))
        run('nohup service {} restart'.format(name))
    else:
        run('nohup service {} start'.format(name))


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


def install_fail2ban():
    require.deb.package(['fail2ban'])
    if not service.is_running('fail2ban'):
        service.start('fail2ban')
