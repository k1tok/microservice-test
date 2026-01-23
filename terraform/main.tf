terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"  
}

# VPC
resource "aws_vpc" "microservices_vpc" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "microservices-vpc"
  }
}

# Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id     = aws_vpc.microservices_vpc.id
  cidr_block = "10.0.1.0/24"
  
  tags = {
    Name = "microservices-public-subnet"
  }
}

# Security Group
resource "aws_security_group" "microservices_sg" {
  name        = "microservices-sg"
  description = "Security group for microservices"
  vpc_id      = aws_vpc.microservices_vpc.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI ports
  ingress {
    from_port   = 8000
    to_port     = 8002
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "microservices-security-group"
  }
}

# EC2 Instance для микросервисов
resource "aws_instance" "microservices_server" {
  ami           = "ami-0c55b159cbfafe1f0"  # Ubuntu 20.04
  instance_type = "t3.medium"
  subnet_id     = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.microservices_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              # Установка Docker
              apt-get update
              apt-get install -y docker.io docker-compose
              
              # Клонирование проекта
              git clone https://github.com/k1tok/microservice-test.git
              cd microservice-test
              
              # Запуск микросервисов
              docker-compose up -d
              EOF

  tags = {
    Name = "microservices-server"
  }
}

# Elastic IP
resource "aws_eip" "microservices_eip" {
  instance = aws_instance.microservices_server.id
  vpc      = true
}

output "server_ip" {
  value = aws_eip.microservices_eip.public_ip
}

output "server_url" {
  value = "http://${aws_eip.microservices_eip.public_ip}:8000"
}