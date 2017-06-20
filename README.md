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

### `fab <my_task>:<my_args> -H <ip_address> -I`
Run a task on a host.  We don't maintain a host list because they are all
expendable, and Cloud at Cost takes forever to spawn servers. **Think
immutable-architecture**. You should have spawned a brand-spanking new
machine to replace another, instead of updating it in-place.

### `fab -l`
Use this to quickly view a list of all tasks.

## Galera Cluster
For recovering stopped nodes read:
[Galera Replication - How to recover a PXC Cluster](https://www.percona.com/blog/2014/09/01/galera-replication-how-to-recover-a-pxc-cluster/)

Read docs on [wresp_cluster_address](http://galeracluster.com/documentation-webpages/mysqlwsrepoptions.html#wsrep-cluster-address)
to understand how they work before you screw up the cluster.

    fab mariadb.build_cluster:<IP_A>,<IP_B>,<IP_ARB> -I
    fab mariadb.add_admin:lgunsch -H <IP_A> -I

There must always be an **odd number of nodes**. If there must be an even number
of nodes, at least have one machine with an arbitrator to make the voting odd.
Another option is to specify some nodes with a higher weight.

Galera keeps state files around that apt will not remove, so even if you
`apt-get purge mariadb-server galera-3` and re-install it, it will try
and re-join its cluster to recover. If weird stuff is happening, build a
fresh set of machines for a new cluster.

**Important**: If the whole cluster is shutdown, you must start up the
cluster by starting the node with the most advanced node state ID. Individual
nodes will refuse to start until that node has first been started.

[Restarting the Cluster]()http://galeracluster.com/documentation-webpages/restartingcluster.html)

For the definition of primary, which is mentioned in the logs a lot, see:

[Primary Component](http://galeracluster.com/documentation-webpages/glossary.html#term-primary-component)


## GlusterFS Cluster
Currently setup as a simple replicate volume between the 3 nodes, without
any distributed volumes.

Warning: **Gluster authenticates it peer nodes hostnames via reverse
DNS. You must have reverse DNS setup before adding peer nodes**.

If you forgot to set the reverse DNS, try and follow the `When you replace a
node` steps.

## When you replace a node
If you are replacing a failed node, but reusing a hostname, do this:

1. Stop GlusterFS
2. Grab the UUID of the failed node from one of the peers.
3. Update `/var/lib/glusterd/glusterd.info` to have the correct
   UUID, as taken from a peer.
4. Now follow: [Resolving Peer Rejected](http://gluster.readthedocs.io/en/latest/Administrator%20Guide/Resolving%20Peer%20Rejected/) 


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
