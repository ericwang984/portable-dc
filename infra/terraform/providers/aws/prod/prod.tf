variable "name" {
  description = "The name of the platform"
  default     = "DCOS"
}

variable "region" {}

variable "vpc_cidr" {
  description = "The IP range of the VPC subnet"
}

variable "site_public_key" {}

# Network
variable "azs" {}

variable "private_slave_subnets" {}
variable "public_slave_subnets" {}
variable "master_subnets" {}

variable "bastion_ami" {}
variable "bastion_instance_type" {}

# Compute

variable "master_ami" {}

variable "master_instance_type" {}
variable "master_node_count" {}

variable "private_slave_ami" {}
variable "private_slave_instance_type" {}
variable "private_slave_node_count" {}

variable "public_slave_ami" {}
variable "public_slave_instance_type" {}
variable "public_slave_node_count" {}

# variable "alb_listener_port" {}

provider "aws" {
  region = "${var.region}"
}

resource "aws_key_pair" "site_key" {
  key_name   = "${var.name}-key"
  public_key = "${file("${var.site_public_key}")}"

  lifecycle {
    create_before_destroy = true
  }
}

module "network" {
  source = "../../../modules/aws/network"

  name                  = "${var.name}"
  vpc_cidr              = "${var.vpc_cidr}"
  azs                   = "${var.azs}"
  private_slave_subnets = "${var.private_slave_subnets}"
  public_slave_subnets  = "${var.public_slave_subnets}"
  master_subnets        = "${var.master_subnets}"
  bastion_ami           = "${var.bastion_ami}"
  bastion_instance_type = "${var.bastion_instance_type}"
  bastion_key_name      = "${aws_key_pair.site_key.key_name}"
}

module "compute" {
  source = "../../../modules/aws/compute"

  name     = "${var.name}"
  vpc_id   = "${module.network.vpc_id}"
  vpc_cidr = "${var.vpc_cidr}"
  key_name = "${aws_key_pair.site_key.key_name}"

  master_amis          = "${var.master_ami}"
  master_instance_type = "${var.master_instance_type}"
  master_node_count    = "${var.master_node_count}"
  master_subnet_ids    = "${module.network.master_subnet_ids}"

  private_slave_amis          = "${var.private_slave_ami}"
  private_slave_instance_type = "${var.private_slave_instance_type}"
  private_slave_node_count    = "${var.private_slave_node_count}"
  private_slave_subnet_ids    = "${module.network.private_subnet_ids}"

  public_slave_amis          = "${var.public_slave_ami}"
  public_slave_instance_type = "${var.public_slave_instance_type}"
  public_slave_node_count    = "${var.public_slave_node_count}"
  public_slave_subnet_ids    = "${module.network.public_subnet_ids}"

  # alb_listener_port          = "${var.alb_listener_port}"
}

output "master_private_ips" {
  value = "${module.compute.master_private_ips}"
}

output "private_slave_private_ips" {
  value = "${module.compute.private_slave_private_ips}"
}

output "public_slave_private_ips" {
  value = "${module.compute.public_slave_private_ips}"
}

output "public_slave_public_ips" {
  value = "${module.compute.public_slave_public_ips}"
}

output "bastion_public_ip" {
  value = "${module.network.bastion_public_ip}"
}
