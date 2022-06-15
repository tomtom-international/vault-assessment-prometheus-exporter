"""
Class for monitoring secret (KV2) expiration information in HashiCorp Vault.
"""

from vault_monitor.expiration_monitor.expiration_monitor import ExpirationMonitor


class SecretExpirationMonitor(ExpirationMonitor):
    """
    Class for monitoring KV2 secrets
    """
    last_renewal_gauge_name = "vault_secret_last_renewal_timestamp"
    last_renewal_gauge_description = "Timestamp for when a secret was last updated."
    expiration_gauge_name = "vault_secret_expiration_timestamp"
    expiration_gauge_description = "Timestamp for when a secret should expire."

    def get_monitored_url(self) -> str:
        """
        Returns a URL for the secret being monitored
        """
        return f"{self.vault_client.url}/v1/{self.mount_point}/metadata/{self.secret_path}"
