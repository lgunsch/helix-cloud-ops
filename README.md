# Overview
These Fabric tasks are not meant to stateful, like Ansible, or Salt. It is
assumed that you have spawned a brand new machine when you run a task,
or set of tasks together. No state checking is done.

# Setup

1. Install vagrant, and virtualbox too if it's not pulled in by vagrant.
2. Install and configure `ssh-agent` (this isn't necessary if you have
   an unsecured vulnerable password-less ssh key).
3. Decrypt your ssh key you use for Github: `ssh-add`
   or `ssh-add ~/.ssh/mykey.pem`
4. Add the below section to your `~/.ssh/config`:
   ```
    Host localhost:2222
      ForwardAgent yes
    Host 127.0.0.1:2222
      ForwardAgent yes
    ```

# Usage:

### `fab <my_task>:<my_args> -IH <ip_address> `
Run a task on a host.  We don't maintain a host list because they are all
expendable, and Cloud at Cost takes forever to spawn servers. **Think
immutable-architecture**. You should have spawned a brand-spanking new
machine to replace another, instead of updating it in-place.

### `fab -l`
Use this to quickly view a list of all tasks.

## Galera Cluster
For recovering stopped nodes read both:
[Resetting the Quorum](http://galeracluster.com/documentation-webpages/quorumreset.html#automatic-bootstrap)
[Galera Replication - How to recover a PXC Cluster](https://www.percona.com/blog/2014/09/01/galera-replication-how-to-recover-a-pxc-cluster/)

Read docs on [wresp_cluster_address](http://galeracluster.com/documentation-webpages/mysqlwsrepoptions.html#wsrep-cluster-address)
to understand how they work before you screw up the cluster.

    fab mariadb.build_cluster:<HOST_A>,<HOST_B>,<HOST_C> -I
    fab mariadb.add_admin:lgunsch -H <IP_A> -I

or

    fab mariadb.install:'<HOST_A>\,<HOST_B>' -IH <HOST_C>
    fab mariadb.start -IH <HOST_C>  # restart after install is required, but install does not make assumptions

There must always be an **odd number of nodes**. If there must be an even number
of nodes, at least have one machine with an arbitrator to make the voting odd.
Another option is to specify some nodes with a higher weight.

Galera keeps state files around that apt will not remove, so even if you
`apt-get purge mariadb-server galera-3` and re-install it, it will try
and re-join its cluster to recover. If weird stuff is happening, build a
fresh set of machines for a new cluster.

**Important**: If the whole cluster is shutdown, you must start up the
cluster by starting the node with the most advanced node state ID. Individual
nodes will refuse to start until that node has first been started. If you
cannot because it's gone, read the below "Cluster is shutdown" section,
as well as the "manual bootstrap" section of [Resetting the Quorum].

[Restarting the Cluster](http://galeracluster.com/documentation-webpages/restartingcluster.html)

For the definition of primary, which is mentioned in the logs a lot, see:

[Primary Component](http://galeracluster.com/documentation-webpages/glossary.html#term-primary-component)

## Cluster is shutdown, and the primary component is permanently failed
*This is a summary of [Restarting the Cluster] and [Resetting the Quorum]
"Manual Bootstrap" section.*

For example, if a whole data-center fails (squinting at you Cloud@Cost), and
it was the primary (which is bad practice). Once you spin up new servers to
replace the ones lost it will take a few steps to get the cluster going again.

1. Stop all MariaDB instances across the cluster, new ones and old ones.
   *MariaDB seems to have trouble with `/etc/init.d/mysql stop`, so you
   may have to also kill processes manually.*
   Note: Ubuntu starts daemons without asking, so *you will have to kill
   MariaDB right after a fresh install*.
2. On one node that is **known to have the complete data set** (likely
   the remaining non-failed server), edit `/var/lib/mysql/grastate.dat`, changing
   `safe_to_bootstrap` to `1`. `safe_to_bootsrap` is a protection which we
   may have to disable since there are no remaining usable servers from
   the primary component.
3. Start that node with `service mysql --wsrep-new-cluster` to create a
   new cluster with it's current saved state.
4. Now start the remaining MariaDB instances to join the new cluster.

**Don't forget to restart HAProxy since it doesn't re-resolve DNS.**


## GlusterFS Cluster
Currently setup as a simple replicate volume between the 3 nodes, without
any distributed volumes.

Warning: **Gluster authenticates it peer nodes hostnames via reverse
DNS. You must have reverse DNS setup before adding peer nodes**.

If you forgot to set the reverse DNS, try and follow the `When you replace a
node` steps.

## When you replace a node
If you are replacing a failed node, but reusing a hostname, do this:

1. Stop GlusterFS: `service glusterfs-server stop`.
2. Grab the UUID of the failed node from one of the good peers:
   `gluster peer status`.
3. Remove everything, except for `glusterd.info` in
   `/var/lib/glusterd/glusterd.info`:
   `rm -Rf bitd/ geo-replication/ glustershd/ groups/ hooks/ nfs/ options `
   ` peers/ quotad/ scrub/ snaps/ ss_brick/ vols/`.
4. Update `/var/lib/glusterd/glusterd.info` to have the correct UUID,
   as taken from a peer earlier.
5. Start GlusterFS: `service glusterfs-service start`
6. Probe a good gluster peer: `gluster peer probe node-1.helix-cloud.ca`
7. Possibly re-start the `glusterfs-service` until it becomes "Peer in Cluster"
8. Make sure all peers have a "proper looking" `gluster pool list`.
9. From the good node: `gluster volume sync HOSTNAME`.

[Resolving Peer Rejected](http://gluster.readthedocs.io/en/latest/Administrator%20Guide/Resolving%20Peer%20Rejected/)


## helix-cloud.ca

### `fab changelog[:branch=BRANCH]`
Add release entries to the `debian/changelog` file using `dch` tool.

Use the `dch` debian tool to add the entries in the correct format
in the spun-up ubuntu build box. Commit the entries into git, bump
and tag your version also if you wish, and finally don't forget to
git push.

### `fab buildpackage[:branch=BRANCH]`
Creates a cleanly built `.deb` package ready for installation.

## Common Problems:
- If git clone asks for your password while configuring the build box,
  then you don't have `ssh-agent` running with your key added using
  `ssh-add`.
- If you have had the changelog box running a long time it might not
  be destroyed upon logging out. You can kill it manually with
  `vagrant destroy -f`
