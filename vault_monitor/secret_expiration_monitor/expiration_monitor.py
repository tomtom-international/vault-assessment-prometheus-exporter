"""
Class for monitoring secrets in Hashicorp Vault.
"""
from typing import Dict, List, Type, TypeVar

import requests
import hvac
from prometheus_client import Gauge

from vault_monitor.secret_expiration_monitor.vault_time import ExpirationMetadata

ExpirationMonitorType = TypeVar("ExpirationMonitorType", bound="ExpirationMonitor")  # pylint: disable=invalid-name


class ExpirationMonitor:
    """
    Monitors and updates a secret in HashiCorp Vault for expiration based on custom metadat.
    """

    secret_last_renewal_timestamp_gauge: Gauge
    secret_expiration_timestamp_gauge: Gauge

    def __init__(self, mount_point: str, secret_path: str, vault_client: hvac.Client, service: str, prometheus_labels: Dict[str, str] = None, metadata_fieldnames: Dict[str, str] = None) -> None:
        """
        Creates an instance of the ExpirationMonitor class.
        """
        self.mount_point = mount_point
        self.secret_path = secret_path
        self.vault_client = vault_client
        self.service = service
        # Add the secret specific labels to the provided labels
        self.prometheus_labels = {"secret_path": secret_path, "mount_point": mount_point, "service": service}

        if prometheus_labels is not None:
            self.prometheus_labels.update(prometheus_labels)

        prometheus_label_keys = list(self.prometheus_labels.keys())

        if metadata_fieldnames is None:
            metadata_fieldnames = {}
        self.last_renewed_timestamp_fieldname = metadata_fieldnames.get("last_renewal_timestamp", "last_renewal_timestamp")
        self.expiration_timestamp_fieldname = metadata_fieldnames.get("expiration_timestamp", "expiration_timestamp")

        self.create_metrics(prometheus_label_keys)

    @classmethod
    def create_metrics(cls: Type[ExpirationMonitorType], prometheus_label_keys: List[str]) -> None:
        """
        Create the metrics, only happens once during the entire lifetime of the exporter (not with every object creation.)
        """
        # Only create the metric once
        if not hasattr(cls, "secret_last_renewal_timestamp_gauge"):
            print(prometheus_label_keys)
            cls.secret_last_renewal_timestamp_gauge = Gauge("vault_secret_last_renewal_timestamp", "Timestamp for when a secret was last updated.", prometheus_label_keys)
        if not hasattr(cls, "secret_expiration_timestamp_gauge"):
            cls.secret_expiration_timestamp_gauge = Gauge("vault_secret_expiration_timestamp", "Timestamp for when a secret should expire.", prometheus_label_keys)

    def update_metrics(self) -> None:
        """
        Update the current value for the metrics.
        """
        response = requests.get(
            f"{self.vault_client.url}/v1/{self.mount_point}/metadata/{self.secret_path}", headers={"X-Vault-Namespace": self.vault_client.adapter.namespace, "X-Vault-Token": self.vault_client.token}
        )
        response.raise_for_status()

        expiration_info = ExpirationMetadata.from_metadata(response.json()["data"]["custom_metadata"], self.last_renewed_timestamp_fieldname, self.expiration_timestamp_fieldname)

        self.secret_last_renewal_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_last_renewal_timestamp())
        self.secret_expiration_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_expiration_timestamp())
