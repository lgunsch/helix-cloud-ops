from fabric.api import env

from . import common, gluster, helix_cloud_ca, load_balancer, mariadb

env.initial_password_prompt = True
env.user = 'root'
