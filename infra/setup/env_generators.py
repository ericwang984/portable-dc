#!/usr/bin/env python

from os import path, chmod
import json
import yaml
from Crypto.PublicKey import RSA

from helpers import (
    get_tfstate_file, convert_list_to_dict, get_nodes_ips, render_template
)


def generate_ansible_cfg(env_path):
    """Render ansible config file in environment path.
    
    Arguments:
        env_path {string} -- The path of the environment path
    """

    cfg_path = path.realpath(path.join(env_path, 'ansible.cfg'))
    ssh_cfg_path = path.realpath(path.join(env_path, 'ssh.cfg'))

    stream = render_template(
        "ansible.cfg.j2", 
        ssh_cfg_path=ssh_cfg_path
    )

    with open(cfg_path, "w") as file_handler:
        file_handler.write(stream)


def generate_inventory(env_path, terraform_path):
    """Format the dictionary of ip addresses to yaml file, and write them to environment folder,
    make it as a inventory file.
    
    Arguments:
        env_path {string} -- The path of environment folder.
        terraform_path {string} -- The path of the terraform working path.
    
    Return:
        dict -- The dictionary of ip addresses that returned by function get_nodes_ips()
    """

    inventory_file = path.realpath(path.join(env_path, 'hosts.yml'))

    tfstate_file = get_tfstate_file(terraform_path)

    nodes_ips_dic = get_nodes_ips(tfstate_file)

    with open(inventory_file, "w") as file_handler:
        stream = yaml.safe_dump(nodes_ips_dic, default_flow_style=False)
        file_handler.write(stream)

    return nodes_ips_dic


def generate_ssh_cfg(env_path, bastion_ip):
    """Render ssh config file in environment path to make it possible to 
    ssh cloud servers with bastion server.
    
    Arguments:
        env_path {string} -- The path of the environment path
        bastion_ip {string} -- The ip address of the bastion server.
    """

    cfg_path = path.realpath(path.join(env_path, 'ssh.cfg'))
    bastion_ip = bastion_ip
    private_key_path = path.realpath(path.join(env_path, 'private.key'))
    ssh_cfg_path = path.realpath(path.join(env_path, 'ssh.cfg'))

    stream = render_template(
        "ssh.cfg.j2", 
        bastion_ip=bastion_ip, 
        private_key_path=private_key_path, 
        ssh_cfg_path=ssh_cfg_path
    )

    with open(cfg_path, "w") as file_handler:
        file_handler.write(stream)


def generate_sshkey_pair(env_path):
    """Generate ssh key pair and write them to env path.
    
    Arguments:
        env_path {string} -- The path of the folder that contain env information, 
        like hosts.yml, ssh.cfg, key pairs and so on.

    Return:
        The path of the private key and public key.
    """
    
    private_key_path = path.realpath(path.join(env_path, "private.key"))
    public_key_path = path.realpath(path.join(env_path, "public.key"))
    if not path.isfile(private_key_path):
        key = RSA.generate(2048)
        with open(private_key_path, 'w') as file_handler:
            chmod(private_key_path, 0600)
            file_handler.write(key.exportKey('PEM'))
        pubkey = key.publickey()
        with open(public_key_path, 'w') as file_handler:
            file_handler.write(pubkey.exportKey('OpenSSH'))
    return private_key_path, public_key_path


def generate_terraform_cfg(provider, terraform_path, env_path, cluster_name):
    """Generate terraform config file and write it to terraform folder.
    
    Arguments:
        providor {string} -- The name of the cloud providor.
        terraform_path {string} -- The path of the terraform folder.
        env_path {string} -- The path of the environment foldeer.
        cluster_name {string} -- The name of the cluster defined by the user.
    """

    terraform_cfg_path = path.realpath(path.join(terraform_path, 'terraform.tfvars'))
    public_key_path = path.realpath(path.join(env_path, 'public.key'))

    template_name = provider + "_terraform.tfvars.j2"

    stream = render_template(template_name, cluster_name=cluster_name, public_key_path=public_key_path)

    with open(terraform_cfg_path, "w") as file_handler:
        file_handler.write(stream)