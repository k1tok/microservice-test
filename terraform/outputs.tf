output "instance_public_ip" {
  value = aws_eip.microservices_eip.public_ip
}

output "api_gateway_url" {
  value = "http://${aws_eip.microservices_eip.public_ip}:8000"
}

output "dict_service_url" {
  value = "http://${aws_eip.microservices_eip.public_ip}:8001"
}

output "task_service_url" {
  value = "http://${aws_eip.microservices_eip.public_ip}:8002"
}