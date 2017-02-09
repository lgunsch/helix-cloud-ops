from fabric.api import env

import helix_cloud_ca

env.initial_password_prompt = True
env.user = 'root'
