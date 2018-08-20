#!/usr/bin/env python

import sys
import json
from os import environ, path

# Terraform libs
from python_terraform import Terraform

# Ansible libs
import shutil
from collections import namedtuple
import ansible.constants as C
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor



def execute_terraform(working_dir):
    """Execute terraform code to setup cloud resources, including servers, networks and so on.
    
    Arguments:
        working_dir {string} -- The path of terraform working direcory.
    
    Returns:
        string -- return_code, stdout, stderr.
    """

    tf = Terraform(working_dir=working_dir)
    hiden_dir = path.realpath(path.join(working_dir, ".terraform"))
    # Init terraform env.
    if not path.isdir(hiden_dir):
        tf.init()

    # Run terraform plan.
    plan_return_code, plan_stdout, plan_stderr = tf.plan()
    
    # If there is no error, the stderr returned is unicode instead of a None type. So have to
    # Check the length of the stderr.
    if len(plan_stderr) == 0:
        print(plan_stdout)
        input_str = raw_input("Do you want to perform these actions? Only 'yes' will be accepted to approve.\n  Enter a value:")
        if input_str == "yes":
            print("Start setting up cloud resources ...")
            return tf.apply(skip_plan=True)
        else:
            print("Apply cancelled.")
            sys.exit()
    else:
        print(plan_stderr)
        sys.exit()
            


def execute_ansible(inventory_path, playbook_path, **kwargs):
    """Execute ansible playbook.
    
    Arguments:
        inventory_path {string} -- The path of the inventory file.
        playbook_path {string} -- The path of the playbook to be executed.
        kwagrs -- Extra varibles for the playbook.

    Return:

    """

    print "Env varible 'ANSIBLE_CONFIG' is '%s' for playbook '%s'" % (
        environ.get('ANSIBLE_CONFIG', 'Not Set'), 
        playbook_path
    )
    print "Running playbook: %s" % playbook_path
    # since API is constructed for CLI it expects certain options to always be set, named tuple 'fakes' 
    # the args parsing options object
    Options = namedtuple(
        'Options', [
            'connection', 'listhosts', 'listtasks', 'listtags', 
            'syntax', 'module_path', 'forks', 'become', 'become_method', 
            'become_user', 'check', 'diff', 'remote_user', 'verbosity'
        ]
    )
    options = Options(
        connection='ssh', listhosts=False, listtasks=False, listtags=False, 
        syntax=False, module_path=None, forks=10, become=True, become_method='sudo', 
        become_user='root', check=False, diff=True, remote_user='centos', verbosity=None
    )
    # initialize needed objects
    loader = DataLoader() # Takes care of finding and reading yaml, json and ini files
    passwords = dict()

    # create inventory, use path to host config file as source or hosts in a comma separated string
    inventory = InventoryManager(loader=loader, sources=inventory_path)

    # variable manager takes care of merging all the different sources to give you 
    # a unifed view of variables available in each context
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager.extra_vars = kwargs

    pbex = PlaybookExecutor(
        playbooks=[playbook_path], 
        inventory=inventory, 
        variable_manager=variable_manager, 
        loader=loader, 
        options=options, 
        passwords=passwords
    )
    result = pbex.run() # most interesting data for a play is actually sent to the callback's methods
    # Remove ansible tmpdir
    shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    return result

