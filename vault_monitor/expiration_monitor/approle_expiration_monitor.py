"""
Class for monitoring AppRole secret id expiration information in HashiCorp Vault.
"""

import requests

from vault_monitor.expiration_monitor.expiration_monitor import ExpirationMonitor
from vault_monitor.expiration_monitor.vault_time import ExpirationMetadata


class ApproleExpirationMonitor(ExpirationMonitor):
    """
    Class for monitoring AppRole secret ids
    """

    last_renewal_gauge_name = "vault_approle_secret_id_last_renewal_timestamp"
    last_renewal_gauge_description = "Timestamp for when an AppRole secret id was last updated."
    expiration_gauge_name = "vault_approle_secret_id_expiration_timestamp"
    expiration_gauge_description = "Timestamp for when an approle secret id should expire."

    def get_expiration_info(self) -> ExpirationMetadata:
        """
        Returns a URL for the secret being monitored
        """
        response = requests.get(
            f"{self.vault_client.url}/v1/identity/entity/id/{self.monitored_path}",
            headers={"X-Vault-Namespace": self.vault_client.adapter.namespace, "X-Vault-Token": self.vault_client.token},
        )
        response.raise_for_status()

        return ExpirationMetadata.from_metadata(response.json()["data"]["metadata"], self.last_renewed_timestamp_fieldname, self.expiration_timestamp_fieldname)

