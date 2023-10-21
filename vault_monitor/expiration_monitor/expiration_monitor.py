"""
Class for monitoring expiration information in HashiCorp Vault.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Type, TypeVar

import hvac
from prometheus_client import Gauge

from vault_monitor.expiration_monitor.vault_time import ExpirationMetadata

ExpirationMonitorType = TypeVar("ExpirationMonitorType", bound="ExpirationMonitor")  # pylint: disable=invalid-name


class ExpirationMonitor(ABC):
    """
    Monitors and updates custom metadata in HashiCorp Vault for expiration based on custom metadata.
    """

    secret_last_renewal_timestamp_gauge: Gauge
    secret_expiration_timestamp_gauge: Gauge

    last_renewal_gauge_name: str
    last_renewal_gauge_description: str
    expiration_gauge_name: str
    expiration_gauge_description: str

    def __init__(
        self, mount_point: str, monitored_path: str, vault_client: hvac.Client, service: str, prometheus_labels: Optional[Dict[str, str]] = None, metadata_fieldnames: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Creates an instance of the ExpirationMonitor class.
        """
        self.mount_point = mount_point
        self.monitored_path = monitored_path
        self.vault_client = vault_client
        self.service = service
        # Add the secret specific labels to the provided labels
        self.prometheus_labels = {"monitored_path": monitored_path, "mount_point": mount_point, "service": service}

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
            cls.secret_last_renewal_timestamp_gauge = Gauge(cls.last_renewal_gauge_name, cls.last_renewal_gauge_description, prometheus_label_keys)
        if not hasattr(cls, "secret_expiration_timestamp_gauge"):
            cls.secret_expiration_timestamp_gauge = Gauge(cls.expiration_gauge_name, cls.expiration_gauge_description, prometheus_label_keys)

    @abstractmethod
    def get_expiration_info(self) -> ExpirationMetadata:
        """
        Abstract method for getting the expiration information
        """

    def update_metrics(self) -> None:
        """
        Update the current value for the metrics.
        """

        expiration_info = self.get_expiration_info()

        self.secret_last_renewal_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_last_renewal_timestamp())
        self.secret_expiration_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_expiration_timestamp())
