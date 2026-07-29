"""
McDonald's Allergen Agent Dedicated Secret Manager Integration
--------------------------------------------------------------
Provides secret retrieval leveraging Google Cloud Secret Manager (or AWS Secrets Manager),
with auditing and secure environment variable fallback.
"""

import os
from typing import Optional

# Optional Google Cloud Secret Manager SDK import
try:
    from google.cloud import secretmanager
    HAS_GCP_SECRET_MANAGER = True
except ImportError:
    HAS_GCP_SECRET_MANAGER = False


class SecretManager:
    """
    Dedicated Secret Manager interface for retrieving API credentials
    and sensitive parameters from Google Cloud Secret Manager or local vault.
    """

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID", "mcdonalds-allergen-lab")

    def get_secret(self, secret_id: str = "gemini-api-key", version: str = "latest") -> str:
        """
        Retrieves a secret payload from Google Cloud Secret Manager,
        falling back gracefully to environment variables.

        Args:
            secret_id (str): Name of the secret in Secret Manager. Defaults to 'gemini-api-key'.
            version (str): Version of the secret. Defaults to 'latest'.

        Returns:
            str: The secret string value or empty string.
        """
        # 1. Attempt GCP Secret Manager API lookup if configured
        if HAS_GCP_SECRET_MANAGER and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8").strip()
                if secret_value:
                    return secret_value
            except Exception as e:
                print(f"[!] SecretManager Notice: Could not fetch '{secret_id}' from GCP Secret Manager ({e}). Using environment fallback.")

        # 2. Environment Variable Fallback
        env_key_map = {
            "gemini-api-key": "GEMINI_API_KEY",
            "db-password": "DB_PASSWORD"
        }
        env_var_name = env_key_map.get(secret_id, secret_id.upper().replace("-", "_"))
        return os.environ.get(env_var_name, "")


# Global Singleton Secret Manager
secret_manager = SecretManager()
