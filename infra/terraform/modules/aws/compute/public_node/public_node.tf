#--------------------------------------------------------------
# This module creates all resources necessary for the
# public nodes.
#--------------------------------------------------------------
#TODO: Write more detailed comments.

variable "name" {}

variable "vpc_id" {}
variable "vpc_cidr" {}
variable "amis" {}
variable "instance_type" {}
variable "nodes" {}
variable "subnet_ids" {}
variable "key_name" {}

# variable "alb_listener_port" {}

# variable "target_group_path" {
#   default = "/"
# }

# variable "target_group_port" {
#   default = "traffic-port"
# }

# variable "svc_port" {
#   default = "80"
# }

resource "aws_security_group" "public_sg" {
  name        = "${var.name}"
  vpc_id      = "${var.vpc_id}"
  description = "Security group for public nodes"

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

resource "aws_security_group" "lb_sg" {
  name        = "${var.name}-elb"
  vpc_id      = "${var.vpc_id}"
  description = "Security group for external ELB"

  tags {
    Name = "${var.name}-elb"
  }

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all traffic in to port 80"
  }

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all traffic in to port 443"
  }

  egress {
    protocol    = -1
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all traffic out"
  }
}

resource "aws_eip" "external_lb_eip" {
  vpc = true

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb" "external_lb" {
  name = "${var.name}-lb"

  load_balancer_type = "network"
  internal           = false
  subnets            = ["${split(",", var.subnet_ids)}"]

  tags {
    Name = "${var.name}-lb"
  }
}

resource "aws_lb_target_group" "public_80" {
  name        = "${var.name}-target-group"
  port        = 80
  protocol    = "TCP"
  vpc_id      = "${var.vpc_id}"
  target_type = "instance"
}

resource "aws_lb_target_group_attachment" "public_80" {
  count            = "${aws_instance.public_node.count}"
  target_group_arn = "${aws_lb_target_group.public_80.arn}"
  target_id        = "${element(aws_instance.public_node.*.id, count.index)}"
  port             = 80
}

resource "aws_lb_listener" "public_80" {
  load_balancer_arn = "${aws_lb.external_lb.id}"
  port              = 80
  protocol          = "TCP"

  "default_action" {
    "target_group_arn" = "${aws_lb_target_group.public_80.id}"
    "type"             = "forward"
  }
}

# resource "aws_alb" "external_alb" {
#   name     = "${var.name}-lb"
#   internal = false

#   subnets         = ["${split(",", var.subnet_ids)}"]
#   security_groups = ["${aws_security_group.lb_sg.id}"]

#   lifecycle {
#     create_before_destroy = true
#   }

#   tags {
#     Name = "${var.name}-lb"
#   }
# }

# resource "aws_alb_listener" "external_alb_http_listener" {
#   load_balancer_arn = "${aws_alb.external_alb.arn}"
#   port              = "${var.alb_listener_port}"
#   protocol          = "HTTP"

#   default_action {
#     target_group_arn = "${aws_alb_target_group.external_alb_target_group.arn}"
#     type             = "forward"
#   }
# }

# resource "aws_alb_target_group" "external_alb_target_group" {
#   name     = "${var.name}-target-group"
#   port     = "${var.svc_port}"
#   protocol = "HTTP"
#   vpc_id   = "${var.vpc_id}"

#   tags {
#     name = "${var.name}-target-group"
#   }

#   health_check {
#     healthy_threshold   = 3
#     unhealthy_threshold = 10
#     timeout             = 5
#     interval            = 10
#     path                = "${var.target_group_path}"
#     port                = "${var.target_group_port}"
#   }
# }

resource "aws_instance" "public_node" {
  ami           = "${element(split(",", var.amis), count.index)}"
  instance_type = "${var.instance_type}"

  tags {
    Name        = "${var.name}-${count.index}"
    Application = "${var.name}"
  }

  count = "${var.nodes}"

  vpc_security_group_ids = ["${aws_security_group.public_sg.id}"]

  subnet_id         = "${element(split(",", var.subnet_ids), count.index)}"
  source_dest_check = false

  key_name                    = "${var.key_name}"
  associate_public_ip_address = true
}

output "private_ips" {
  value = "${join(",", aws_instance.public_node.*.private_ip)}"
}

output "public_ips" {
  value = "${join(",", aws_instance.public_node.*.public_ip)}"
}
