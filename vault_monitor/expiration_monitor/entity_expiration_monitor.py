"""
Class for monitoring entity secret expiration information in HashiCorp Vault.
"""

from typing import Optional, Dict

import requests
import hvac

from vault_monitor.expiration_monitor.expiration_monitor import ExpirationMonitor
from vault_monitor.expiration_monitor.vault_time import ExpirationMetadata

TIMEOUT = 60


class EntityExpirationMonitor(ExpirationMonitor):
    """
    Class for monitoring entity secrets
    """

    last_renewal_gauge_name = "vault_entity_last_renewal_timestamp"
    last_renewal_gauge_description = "Timestamp for when an entity's secrets were last updated."
    expiration_gauge_name = "vault_entity_expiration_timestamp"
    expiration_gauge_description = "Timestamp for when an entity's secrets should be expired and rotated."

    def __init__(
        self,
        mount_point: str,
        monitored_path: str,
        name: str,
        vault_client: hvac.Client,
        service: str,
        prometheus_labels: Optional[Dict[str, str]] = None,
        metadata_fieldnames: Optional[Dict[str, str]] = None,
    ) -> None:
        if prometheus_labels:
            prometheus_labels.update({"entity_name": name})
        else:
            prometheus_labels = {"entity_name": name}
        super().__init__(mount_point, monitored_path, vault_client, service, prometheus_labels, metadata_fieldnames)

    def get_expiration_info(self) -> ExpirationMetadata:
        """
        Returns a URL for the entity being monitored
        """
        response = requests.get(
            f"{self.vault_client.url}/v1/identity/entity/id/{self.monitored_path}",
            headers={"X-Vault-Namespace": self.vault_client.adapter.namespace, "X-Vault-Token": self.vault_client.token},
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        return ExpirationMetadata.from_metadata(response.json()["data"]["metadata"], self.last_renewed_timestamp_fieldname, self.expiration_timestamp_fieldname)
