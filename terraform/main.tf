# ==============================================================================
# Infrastructure as Code (IaC) - Terraform Main Configuration
# McDonald's Allergen AI Agent Deployment on GCP Cloud Run & Secret Manager
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 1. Enable GCP API Services
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Service Account for Allergen Agent
resource "google_service_account" "agent_sa" {
  account_id   = "mcdonalds-allergen-agent-sa"
  display_name = "McDonald's Allergen AI Agent Service Account"
  depends_on   = [google_project_service.services]
}

# 3. Secret Manager Secret for Gemini API Key
resource "google_secret_manager_secret" "gemini_api_key_secret" {
  secret_id = "gemini-api-key"
  replication {
    user_managed {
      replicas {
        location = var.gcp_region
      }
    }
  }
  depends_on = [google_project_service.services]
}

# Grant Service Account Secret Access
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.gemini_api_key_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

# 4. Cloud Run Service Deployment
resource "google_cloud_run_v2_service" "allergen_agent_service" {
  name     = "mcdonalds-allergen-ai-agent"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.agent_sa.email

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
      }

      ports {
        container_port = 8000
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.gcp_project_id
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key_secret.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/api/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.secret_accessor
  ]
}

# 5. Public IAM Policy for Web UI Access
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  name     = google_cloud_run_v2_service.allergen_agent_service.name
  location = google_cloud_run_v2_service.allergen_agent_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
