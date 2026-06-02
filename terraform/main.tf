terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

# ── Namespace ─────────────────────────────────────────────────
resource "kubernetes_namespace" "fraud_detection" {
  metadata {
    name = var.namespace
    labels = {
      app        = "fraud-detection"
      monitoring = "prometheus"
    }
  }
}

# ── Deployment (controls ReplicaSet with 3 pods) ──────────────
resource "kubernetes_deployment" "fraud_detection" {
  metadata {
    name      = "fraud-detection"
    namespace = kubernetes_namespace.fraud_detection.metadata[0].name
    labels    = { app = "fraud-detection" }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = { app = "fraud-detection" }
    }

    template {
      metadata {
        labels = { app = "fraud-detection" }
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = tostring(var.app_port)
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        container {
          name              = "fraud-detection"
          image             = var.docker_image
          image_pull_policy = "Always"

          port {
            container_port = var.app_port
          }

          resources {
            limits   = { cpu = "500m", memory = "512Mi" }
            requests = { cpu = "250m", memory = "256Mi" }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = var.app_port
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = var.app_port
            }
            initial_delay_seconds = 15
            period_seconds        = 5
          }

          env {
            name  = "MODEL_PATH"
            value = "models/fraud_model.pkl"
          }
        }
      }
    }
  }

  wait_for_rollout = true
}

# ── Service (NodePort for external access) ────────────────────
resource "kubernetes_service" "fraud_detection" {
  metadata {
    name      = "fraud-detection-svc"
    namespace = kubernetes_namespace.fraud_detection.metadata[0].name
    labels    = { app = "fraud-detection" }
  }

  spec {
    selector = { app = "fraud-detection" }
    type     = "NodePort"

    port {
      port        = 80
      target_port = var.app_port
      node_port   = 30080
    }
  }
}
