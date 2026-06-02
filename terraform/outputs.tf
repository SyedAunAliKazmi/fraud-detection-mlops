output "namespace" {
  value = kubernetes_namespace.fraud_detection.metadata[0].name
}

output "service_name" {
  value = kubernetes_service.fraud_detection.metadata[0].name
}

output "replicas" {
  value       = var.replicas
  description = "Number of pods in ReplicaSet"
}

output "node_port" {
  value       = 30080
  description = "NodePort for accessing the API"
}
