import requests
from prometheus_client import Gauge


from expiration_monitor.vault_time import expirationMetadata


class expirationMonitor:
    def __init__(self, mount_point: str, secret_path: str, vault_client, service: str, prometheus_labels: dict, metadata_fieldnames: dict) -> None:
        self.mount_point = mount_point
        self.secret_path = secret_path
        self.vault_client = vault_client
        self.service = service
        self.prometheus_labels = prometheus_labels

        self.secret_last_renewal_timestamp_gauge = Gauge(f"secret_{self.__get_metric_base_name()}_last_renewal_timestamp", "Timestamp for when the secret was last updated.", prometheus_labels.keys())
        self.secret_expiration_timestamp_gauge = Gauge(f"secret_{self.__get_metric_base_name()}_expiration_timestamp", "Timestamp for when the secret should expire.", prometheus_labels.keys())

        self.last_renewed_timestamp_fieldname = metadata_fieldnames.get("last_renewal_timestamp", "last_renewal_timestamp")
        self.expiration_timestamp_fieldname = metadata_fieldnames.get("expiration_timestamp", "expiration_timestamp")

    def update_metrics(self) -> None:
        response = requests.get(
            f"{self.vault_client.url}/v1/{self.mount_point}/metadata/{self.secret_path}", headers={"X-Vault-Namespace": self.vault_client.adapter.namespace, "X-Vault-Token": self.vault_client.token}
        )

        expiration_info = expirationMetadata.fromMetadata(response.json()["data"]["custom_metadata"], self.last_renewed_timestamp_fieldname, self.expiration_timestamp_fieldname)

        self.secret_last_renewal_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_last_renewal_timestamp())
        self.secret_expiration_timestamp_gauge.labels(**self.prometheus_labels).set(expiration_info.get_expiration_timestamp())

    def __get_metric_base_name(self) -> str:
        return self.mount_point.replace("/", "_") + "_" + self.secret_path.replace("/", "_")
