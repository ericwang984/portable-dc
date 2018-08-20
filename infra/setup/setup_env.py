#!/usr/bin/env python

import argparse
import sys
from os import path, makedirs, environ
from env_generators import (
    generate_ansible_cfg, generate_inventory, generate_ssh_cfg,
    generate_sshkey_pair, generate_terraform_cfg,
)
from code_executor import (
    execute_ansible, execute_terraform,
)
from helpers import get_bastion_ip, check_ssh


def get_args():
    """Parse argument for the script.
    
    Returns:
        object -- the object contains the arguments of the script.
    """ 

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--provider', '-p', dest='provider', choices=['aws', 'gcp'], required=True,
                        help='Give the provider name, like aws or gcp')
    parser.add_argument('--env', '-e', dest='env', choices=['prod','staging'], required=True,
                        help='Give the type of environment, like prod or staging')
    parser.add_argument('--cluster', '-c', dest='cluster', choices=['dcos','k8s'], required=True,
                        help='Give the type of cluster, like dcos or k8s')
    parser.add_argument('--name', '-n', dest='name', required=True,
                        help='The name of the cluster')

    args = parser.parse_args()
    return args

def get_terraform_path(args):
    """Get the path of the terraform code path according the script arguments.
    
    Arguments:
        args {object} -- The object of the script argument.

    Returns:
        string -- The string of the terraform code path.
    """

    current_path = path.dirname(path.realpath(__file__))
    terraform_path = path.realpath(path.join(
        current_path, '../terraform/providers/',args.provider, args.env
    ))

    if path.isdir(terraform_path):
        return terraform_path
    else:
        raise Exception("The terraform path %s doesn't exists." % terraform_path)

def get_ansible_path(args):
    """Get the path of the ansible code path according the script arguments.
    
    Arguments:
        args {object} -- The object of the script argument.

    Returns:
        string -- The string of the ansible code path.
    """

    current_path = path.dirname(path.realpath(__file__))
    ansible_path = path.realpath(path.join(
        current_path, '../ansible/',args.cluster
    ))

    if path.isdir(ansible_path):
        return ansible_path
    else:
        raise Exception("The ansible path %s doesn't exists." % ansible_path)

def get_env_path(args):
    """Get the path of the the folder that contain hosts.yml and ssh.cfg. If the folder
    doesn't exists, create it.
    
    Arguments:
        args {object} -- The object of the script argument.

    Returns:
        string -- The string of the env environment path.
    """

    current_path = path.dirname(path.realpath(__file__))
    env_path = path.realpath(path.join(
        current_path, './env/',args.provider, args.env, args.cluster
    ))

    try: 
        makedirs(env_path)
    except OSError:
        if path.isdir(env_path):
            return env_path
        else:
            raise
    else:
        return env_path  


def main():
    # Get the argument of the script.
    args = get_args()
    # Get the terraform folder.
    terraform_path = get_terraform_path(args)
    # Get the ansible folder.
    ansible_path = get_ansible_path(args)
    # Get or create environment folder.
    env_path = get_env_path(args)
    # Get the cluster name from the arguments.
    cluster_name = args.name
    provider_name = args.provider

    print("Generating key pair ...")
    private_key, public_key = generate_sshkey_pair(env_path)
    print("Generated key pair successfully.")

    print("Generating terraform cfg file ...")
    generate_terraform_cfg(provider_name, terraform_path, env_path, cluster_name)
    print("Generated terraform cfg successfully.")

    print("Executing terraform code to create cloud resources ...")
    print("Terraform working dir is %s" % terraform_path)
    terra_return_code, terra_stdout, terra_stderr = execute_terraform(terraform_path)
    # If there is no error, the stderr returned is unicode instead of a None type. So have to
    # Check the length of the stderr.
    if len(terra_stderr) == 0:
        print("Executed terraform code to create cloud resources successfully.")
    else:
        print(terra_stderr)
        sys.exit()

    # Get the bastion ip and generate ssh config file.
    nodes_ips_dict = generate_inventory(env_path, terraform_path)
    bastion_ip = get_bastion_ip(nodes_ips_dict)
    generate_ssh_cfg(env_path, bastion_ip)

    # Generate ansible config file.
    generate_ansible_cfg(env_path)

    # Check the ssh availbility of bastion server.
    is_bastion_available = check_ssh(bastion_ip, 'centos', private_key)

    # Run ansbile playbooks when the bastion is available.
    if is_bastion_available:
        # Get inventory file path.
        inventory_path = path.realpath(path.join(env_path, 'hosts.yml'))
        # Get playbooks' path.
        bootstrap_playbook = path.realpath(path.join(ansible_path, 'bootstrap.yml'))
        master_playbook = path.realpath(path.join(ansible_path, 'master.yml'))
        public_slave_playbook = path.realpath(path.join(ansible_path, 'public_slave.yml'))
        private_slave_playbook = path.realpath(path.join(ansible_path, 'private_slave.yml'))

        # Set environment varible "ANSIBLE_CONFIG" for ansible.
        ansible_cfg_path = path.realpath(path.join(env_path, 'ansible.cfg'))
        environ["ANSIBLE_CONFIG"] = ansible_cfg_path
        print "Set env varible 'ANSIBLE_CONFIG' to: %s" % environ.get('ANSIBLE_CONFIG', 'Not Set')
        print("Executing ansible playbooks ...")
        bootstrap_result = execute_ansible(inventory_path, bootstrap_playbook, dcos_cluster_name=cluster_name)
        if bootstrap_result != 0:
            print("Something wrong when executing bootstrap playbook.")
            sys.exit()
        master_result = execute_ansible(inventory_path, master_playbook, dcos_cluster_name=cluster_name)
        if master_result != 0:
            print("Something wrong when executing master playbook.")
            sys.exit()
        public_slave_result = execute_ansible(inventory_path, public_slave_playbook, dcos_cluster_name=cluster_name)
        if public_slave_result != 0:
            print("Something wrong when executing public slave playbook.")
            sys.exit()
        private_slave_result = execute_ansible(inventory_path, private_slave_playbook, dcos_cluster_name=cluster_name)
        if private_slave_result != 0:
            print("Something wrong when executing private slave playbook.")
            sys.exit()
        print("Executed ansible playbooks successfully.")
    else:
        print("Bastion is not available.")

if __name__ == '__main__':
    main()