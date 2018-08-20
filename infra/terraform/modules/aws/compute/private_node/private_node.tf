#--------------------------------------------------------------
# This module creates all resources necessary for the
# private nodes.
#--------------------------------------------------------------

variable "name" {
  default = "private"
}

variable "vpc_id" {}
variable "vpc_cidr" {}
variable "amis" {}
variable "instance_type" {}
variable "nodes" {}
variable "subnet_ids" {}
variable "key_name" {}

resource "aws_security_group" "private_sg" {
  name        = "${var.name}"
  vpc_id      = "${var.vpc_id}"
  description = "Security group for private nodes"

  tags {
    Name = "${var.name}"
  }

  lifecycle {
    create_before_destroy = true
  }

  ingress {
    protocol    = -1
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["${var.vpc_cidr}"]
    description = "Allow all traffic in the vpc in"
  }

  egress {
    protocol    = -1
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all traffic out"
  }
}

resource "aws_instance" "private_node" {
  ami           = "${element(split(",", var.amis), count.index)}"
  instance_type = "${var.instance_type}"

  tags {
    Name        = "${var.name}-${count.index}"
    Application = "${var.name}"
  }

  count = "${var.nodes}"

  vpc_security_group_ids = ["${aws_security_group.private_sg.id}"]

  subnet_id         = "${element(split(",", var.subnet_ids), count.index)}"
  source_dest_check = false

  key_name                    = "${var.key_name}"
  associate_public_ip_address = false
}

output "private_ips" {
  value = "${join(",", aws_instance.private_node.*.private_ip)}"
}
