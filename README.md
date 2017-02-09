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

### `fab <my_task> -H <ip_address> -I`
Run a task on a host.  We don't maintain a host list because they are all
expendable. Think immutable-architecture. You should have spawned a
brand-spanking new machine to replace another, instead of updating
it in-place.

### `fab -l`
Use this to quickly view a list of all tasks.

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
