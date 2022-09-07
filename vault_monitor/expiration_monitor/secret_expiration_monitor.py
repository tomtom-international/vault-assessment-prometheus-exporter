"""
Class for monitoring secret (KV2) expiration information in HashiCorp Vault.
"""

import requests

from vault_monitor.expiration_monitor.expiration_monitor import ExpirationMonitor
from vault_monitor.expiration_monitor.vault_time import ExpirationMetadata

TIMEOUT = 60


class SecretExpirationMonitor(ExpirationMonitor):
    """
    Class for monitoring KV2 secrets
    """

    last_renewal_gauge_name = "vault_secret_last_renewal_timestamp"
    last_renewal_gauge_description = "Timestamp for when a secret was last updated."
    expiration_gauge_name = "vault_secret_expiration_timestamp"
    expiration_gauge_description = "Timestamp for when a secret should expire."

    def get_expiration_info(self) -> ExpirationMetadata:
        """
        Returns a URL for the secret being monitored
        """
        response = requests.get(
            f"{self.vault_client.url}/v1/{self.mount_point}/metadata/{self.monitored_path}",
            headers={"X-Vault-Namespace": self.vault_client.adapter.namespace, "X-Vault-Token": self.vault_client.token},
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        return ExpirationMetadata.from_metadata(response.json()["data"]["custom_metadata"], self.last_renewed_timestamp_fieldname, self.expiration_timestamp_fieldname)
