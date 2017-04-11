from fabric.api import env

from . import helix_cloud_ca, load_balancer, mariadb, common

env.initial_password_prompt = True
env.user = 'root'
