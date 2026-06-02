variable "docker_image" {
  description = "Docker image for the fraud detection app"
  type        = string
  default     = "aun12/fraud-detection:latest"
}

variable "replicas" {
  description = "Number of ReplicaSet pods"
  type        = number
  default     = 3
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "fraud-detection"
}

variable "app_port" {
  description = "Application container port"
  type        = number
  default     = 8000
}
