#!/usr/bin/env python

import sys
import json
import time
from os import path
from jinja2 import Environment, FileSystemLoader
from paramiko import SSHClient, AutoAddPolicy
from python_terraform import Terraform


def render_template(template_name, **kwargs):
    """Render a template with the arguments passed in.
    
    Arguments:
        template_name {string} -- The name of the template file.
    
    Returns:
        string -- The string of the file that rendered by the template.
    """

    # Capture our current directory
    current_path = path.dirname(path.realpath(__file__))
    template_folder = path.realpath(path.join(
        current_path, './templates/'
    ))
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = Environment(loader=FileSystemLoader(template_folder),
                         trim_blocks=True)
    return j2_env.get_template(template_name).render(
        **kwargs
    )


def get_tfstate_file(terraform_path):
    """Get the path of the tfstate file.
    
    Arguments:
        terraform_path {string} -- The path of the terraform environment.
    
    Returns:
        string -- The path of the terraform environment.
    """

    tfstate_file = path.realpath(path.join(terraform_path, 'terraform.tfstate'))

    if path.isfile(tfstate_file):
        return tfstate_file
    else:
        raise Exception("The tfstate file in %s doesn't exists." % tfstate_file)


def convert_list_to_dict(from_list):
    """Convert a list to a dictionary. For example, the list passed in is:
    [a, b, c], return a dictionary: {"ansible_host": "a", "ansible_host": "b", "ansible_host": "c"}
    
    Arguments:
        from_list {list} -- A list need to be convert.
    
    Returns:
        dict -- A dictionary.
    """

    to_dict = {}
    for item in from_list:
        to_dict[item] = {"ansible_host": item}
    return to_dict


def get_nodes_ips(tfstate_file):
    """Get the ip address of the nodes created by terraform form the tfstate file.
    
    Arguments:
        tfstate_file {string} -- The path of the tfstate file.
    
    Raises:
        Exception -- [description]
    
    Returns:
        dict -- A dictionary of ip addresses, like:
        {
            "bastion": {
                "hosts": {
                    123.123.123.123:
                        ansible_host: 123.123.123.123
                }
            },
            "private_slave": {
                "hosts": {
                    111.222.111.222:
                        ansible_host: 111.222.111.222
                    111.123.123.123:
                        ansible_host: 111.123.123.123
                }
            }
        }
    """

    nodes_ips_dict = {}
    with open(tfstate_file) as f:
        data = json.load(f)
        nodes_ips = data["modules"][0]["outputs"]

    if nodes_ips:
        if nodes_ips["bastion_public_ip"]["value"]:
            nodes_ips_dict["bastion"] = { 
                "hosts": convert_list_to_dict(nodes_ips["bastion_public_ip"]["value"].split(","))
            }
        if nodes_ips["master_private_ips"]["value"]:
            nodes_ips_dict["master"] = {
                "hosts": convert_list_to_dict(nodes_ips["master_private_ips"]["value"].split(","))
            }
        if nodes_ips["private_slave_private_ips"]["value"]:
            nodes_ips_dict["private_slave"] = {
                "hosts": convert_list_to_dict(nodes_ips["private_slave_private_ips"]["value"].split(","))
            }
        if nodes_ips["public_slave_private_ips"]["value"]:
            nodes_ips_dict["public_slave"] = {
                "hosts": convert_list_to_dict(nodes_ips["public_slave_private_ips"]["value"].split(","))
            }
    else:
        raise Exception("The nodes' ip addresses don't exist in the tfstate file.")
    
    return nodes_ips_dict
    

def get_bastion_ip(nodes_ips_dict):
    """Get the bastion ip address from the dictionary of node ips.
    
    Arguments:
        nodes_ips_dict {dict} -- The dictionary of node ip addresses.
    
    Returns:
        string -- The ip address of bastion node.
    """

    return nodes_ips_dict["bastion"]["hosts"].keys()[0]


def check_ssh(ip, user, key_file):
    """Check the ssh availability of the a server.
    
    Arguments:
        ip {string} -- The ip address of the server.
        user {string} -- The user name to ssh the server
        key_file {string} -- The path of the key file
    
    Returns:
        Boolean -- Return True if the server can be ssh.
    """

    interval = 20
    retries = 15
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    for _ in range(retries):
        try:
            ssh.connect(ip, username=user, key_filename=key_file)
            print("Bastion is available.")
            return True
        except Exception, e:
            print("Waiting for the server to be ready ...")
            time.sleep(interval)
    print("Failed to ssh the server %s" % ip)
    print(e)
    return False


