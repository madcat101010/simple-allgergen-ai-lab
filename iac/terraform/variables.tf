variable "gcp_project_id" {
  type        = string
  description = "Google Cloud Project ID"
  default     = "mcdonalds-allergen-lab"
}

variable "gcp_region" {
  type        = string
  description = "Google Cloud Region"
  default     = "us-central1"
}

variable "container_image" {
  type        = string
  description = "Docker Container Image URI"
  default     = "gcr.io/mcdonalds-allergen-lab/mcdonalds-allergen-ai-agent:latest"
}
