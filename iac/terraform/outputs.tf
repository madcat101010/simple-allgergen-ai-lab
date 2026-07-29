output "cloud_run_url" {
  value       = google_cloud_run_v2_service.allergen_agent_service.uri
  description = "Public URL of the deployed Cloud Run service"
}

output "secret_manager_id" {
  value       = google_secret_manager_secret.gemini_api_key_secret.id
  description = "Secret Manager secret ID"
}
