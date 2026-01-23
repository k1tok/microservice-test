variable "aws_region" {
  description = "AWS region"
  default     = "eu-west-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.medium"
}

variable "ssh_key_name" {
  description = "Name of SSH key pair"
  default     = "microservices-key"
}