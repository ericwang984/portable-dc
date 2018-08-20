#--------------------------------------------------------------
# This module creates all networking resources
#--------------------------------------------------------------

variable "name" {
  description = "The name of the platform"
}

variable "vpc_cidr" {
  description = "The IP range of the VPC subnet"
}

variable "azs" {}
variable "public_slave_subnets" {}
variable "private_slave_subnets" {}
variable "master_subnets" {}

variable "bastion_ami" {}
variable "bastion_instance_type" {}
variable "bastion_key_name" {}

module "vpc" {
  source = "./vpc"

  name     = "${var.name}-vpc"
  vpc_cidr = "${var.vpc_cidr}"
}

module "nat" {
  source = "./nat"

  name              = "${var.name}-nat"
  azs               = "${var.azs}"
  public_subnet_ids = "${module.public_subnet.subnet_ids}"
}

module "public_subnet" {
  source = "./public_subnet"

  name   = "${var.name}-public"
  vpc_id = "${module.vpc.vpc_id}"
  cidrs  = "${var.public_slave_subnets}"
  azs    = "${var.azs}"
}

module "private_subnet" {
  source = "./private_subnet"

  name   = "${var.name}-private"
  vpc_id = "${module.vpc.vpc_id}"
  cidrs  = "${var.private_slave_subnets}"
  azs    = "${var.azs}"

  nat_gateway_ids = "${module.nat.nat_gateway_ids}"
}

module "master_subnet" {
  source = "./private_subnet"

  name   = "${var.name}-master"
  vpc_id = "${module.vpc.vpc_id}"
  cidrs  = "${var.master_subnets}"
  azs    = "${var.azs}"

  nat_gateway_ids = "${module.nat.nat_gateway_ids}"
}

module "bastion" {
  source = "./bastion"

  name              = "${var.name}-bastion"
  vpc_id            = "${module.vpc.vpc_id}"
  vpc_cidr          = "${module.vpc.vpc_cidr}"
  public_subnet_ids = "${module.public_subnet.subnet_ids}"
  key_name          = "${var.bastion_key_name}"
  ami               = "${var.bastion_ami}"
  instance_type     = "${var.bastion_instance_type}"
}

resource "aws_network_acl" "acl" {
  vpc_id     = "${module.vpc.vpc_id}"
  subnet_ids = ["${concat(split(",", module.public_subnet.subnet_ids), split(",", module.private_subnet.subnet_ids), split(",", module.master_subnet.subnet_ids))}"]

  ingress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags {
    Name = "${var.name}-all"
  }
}

# VPC
output "vpc_id" {
  value = "${module.vpc.vpc_id}"
}

output "vpc_cidr" {
  value = "${module.vpc.vpc_cidr}"
}

# Subnet
output "public_subnet_ids" {
  value = "${module.public_subnet.subnet_ids}"
}

output "private_subnet_ids" {
  value = "${module.private_subnet.subnet_ids}"
}

output "master_subnet_ids" {
  value = "${module.master_subnet.subnet_ids}"
}

output "bastion_public_ip" {
  value = "${module.bastion.public_ip}"
}

# NAT
output "nat_gateway_ids" {
  value = "${module.nat.nat_gateway_ids}"
}
