#--------------------------------------------------------------
# This module creates all compute resources
#--------------------------------------------------------------

variable "name" {}

variable "vpc_id" {}
variable "key_name" {}
variable "vpc_cidr" {}

variable "master_amis" {}
variable "master_instance_type" {}
variable "master_node_count" {}
variable "master_subnet_ids" {}

variable "private_slave_amis" {}
variable "private_slave_instance_type" {}
variable "private_slave_node_count" {}
variable "private_slave_subnet_ids" {}

variable "public_slave_amis" {}
variable "public_slave_instance_type" {}
variable "public_slave_node_count" {}
variable "public_slave_subnet_ids" {}

# variable "alb_listener_port" {}

module "master" {
  source = "./private_node"

  name          = "${var.name}-master"
  vpc_id        = "${var.vpc_id}"
  vpc_cidr      = "${var.vpc_cidr}"
  key_name      = "${var.key_name}"
  subnet_ids    = "${var.master_subnet_ids}"
  amis          = "${var.master_amis}"
  nodes         = "${var.master_node_count}"
  instance_type = "${var.master_instance_type}"
}

module "private_slave" {
  source = "./private_node"

  name          = "${var.name}-private"
  vpc_id        = "${var.vpc_id}"
  vpc_cidr      = "${var.vpc_cidr}"
  key_name      = "${var.key_name}"
  subnet_ids    = "${var.private_slave_subnet_ids}"
  amis          = "${var.private_slave_amis}"
  nodes         = "${var.private_slave_node_count}"
  instance_type = "${var.private_slave_instance_type}"
}

module "public_slave" {
  source = "./public_node"

  name          = "${var.name}-public"
  vpc_id        = "${var.vpc_id}"
  vpc_cidr      = "${var.vpc_cidr}"
  key_name      = "${var.key_name}"
  subnet_ids    = "${var.public_slave_subnet_ids}"
  amis          = "${var.public_slave_amis}"
  nodes         = "${var.public_slave_node_count}"
  instance_type = "${var.public_slave_instance_type}"

  # alb_listener_port = "${var.alb_listener_port}"
}

output "master_private_ips" {
  value = "${module.master.private_ips}"
}

output "private_slave_private_ips" {
  value = "${module.private_slave.private_ips}"
}

output "public_slave_private_ips" {
  value = "${module.public_slave.private_ips}"
}

output "public_slave_public_ips" {
  value = "${module.public_slave.public_ips}"
}
