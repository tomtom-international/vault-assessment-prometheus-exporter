import requests
from typing import Dict, List
from prometheus_client import Gauge

from expiration_monitor.vault_time import expirationMetadata


class expirationMonitor:
    def __init__(
        self, mount_point: str, secret_path: str, vault_client, service: str, prometheus_labels: Dict[str, str], prometheus_label_keys: List[str], metadata_fieldnames: Dict[str, str]
    ) -> None:
        self.mount_point = mount_point
        self.secret_path = secret_path
        self.vault_client = vault_client
        self.service = service
        # Add the secret specific labels to the provided labels
        self.prometheus_labels = {"secret_path": secret_path, "mount_point": mount_point, "service": service}
        self.prometheus_labels.update(prometheus_labels)

        prometheus_label_keys += ["secret_path", "mount_point", "service"]

        self.last_renewed_timestamp_fieldname = metadata_fieldnames.get("last_renewal_timestamp", "last_renewal_timestamp")
        self.expiration_timestamp_fieldname = metadata_fieldnames.get("expiration_timestamp", "expiration_timestamp")

        self.create_metrics(prometheus_label_keys)

    @classmethod
    def create_metrics(cls, prometheus_label_keys):
        # Only create the metric once
        if not hasattr(cls, "secret_last_renewal_timestamp_gauge"):
            cls.secret_last_renewal_timestamp_gauge = Gauge(f"vault_secret_last_renewal_timestamp", "Timestamp for when a secret was last updated.", prometheus_label_keys)
        if not hasattr(cls, "secret_expiration_timestamp_gauge"):
            cls.secret_expiration_timestamp_gauge = Gauge(f"vault_secret_expiration_timestamp", "Timestamp for when a secret should expire.", prometheus_label_keys)

    def update_metrics(self) -> None:
        response = requests.get(
            f"{self.vault_client.url}/v1/{self.mount_point}/metadata/{self.secret_path}", headers={"X-Vault-Namespace": self.vault_client.adapter.namespace, "X-Vault-Token": self.vault_client.token}
        )
        response.raise_for_status()

        expiration_info = expirationMetadata.fromMetadata(response.json()["data"]["custom_metadata"], self.last_renewed_timestamp_fieldname, self.expiration_timestamp_fieldname)

        self.secret_last_renewal_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_last_renewal_timestamp())
        self.secret_expiration_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_expiration_timestamp())
