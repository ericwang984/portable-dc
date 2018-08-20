# Portable Data Center

## Overview

This project is to setup infrastructure resources on cloud provider, like AWS or GCP, and then create a cluster (dcos or k8s) with these resouces. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

You need to install `git` on your local machine to clone the code from Github.

If you are using `ubuntu` os, run the command below to install git.

```sh
apt-get install git-core
```

You need `pip` to install python dependant packages.

If you are using `ubuntu` os, run the command below to install it.

```sh
sudo easy_install pip
```

Setup cloud provider auth information in your environment variable.

For example, if you are using `ubuntu` os, set the AWS auth infor in the `~/.bashrc`.

```
export AWS_ACCESS_KEY_ID="xxxxxxxx"
export AWS_SECRET_ACCESS_KEY="yyyyyyyyyyyyyyyyy"
```

### Installing

Get the code from Github.

```
git clone ...
```

Install dependant packages.

```
pip install -r requirements.txt
```

### Usage

Create cloud resources on AWS and setup DCOS cluster on these resources.

```
cd setup
python setup_env.py -p aws -e prod -c dcos -n dcos-demo
```

The usage of `setup_env.py`.

```sh
python setup_env.py --help

usage: setup_env.py [-h] --provider {aws,gcp} --env {prod,staging} --cluster
                    {dcos,k8s} --name NAME

Process some integers.

optional arguments:
  -h, --help            show this help message and exit
  --provider {aws,gcp}, -p {aws,gcp}
                        Give the provider name, like aws or gcp
  --env {prod,staging}, -e {prod,staging}
                        Give the type of environment, like prod or staging
  --cluster {dcos,k8s}, -c {dcos,k8s}
                        Give the type of cluster, like dcos or k8s
  --name NAME, -n NAME  The name of the cluster

```

If you want to change the numbers or types of aws servers, you can change the configurations in `setup/templates/aws_terraform.tfvars.j2`.

The configurations you can change are:

```
bastion_instance_type = ""

master_instance_type = ""

master_node_count = ""

private_slave_instance_type = ""

private_slave_node_count = ""

public_slave_instance_type = ""

public_slave_node_count = ""
```


## Roadmap

  - [X] Create resources on AWS and setup DCOS cluster
  - [ ] Destroy resources
  - [ ] Create resources on AWS and setup K8S cluster
  - [ ] Create resources on GCP and setup DCOS cluster
  - [ ] Create resources on GCP and setup K8S cluster










