import logging
from copy import deepcopy
from typing import List, Dict

from vault_monitor.expiration_monitor.expiration_monitor import expirationMonitor


def create_monitors(config: Dict, vault_client) -> List[expirationMonitor]:
    default_prometheus_labels = config.get("prometheus_labels", {})
    prometheus_label_keys = list(default_prometheus_labels.keys())
    default_metadata_filenames = config.get("metadata_fieldnames", {"last_renewal_timestamp": "last_renewal_timestamp", "expiration_timestamp": "expiration_timestamp"})

    secret_monitors = []
    for secret_config in config.get("services", {}):
        for service, service_config in secret_config.items():
            logging.info("Configuring monitoring for service %s", service)
            # Use deepcopy since dicts are handled by ref and tend to get overwritten otherwise
            service_prometheus_labels = deepcopy(default_prometheus_labels)
            service_prometheus_labels.update(service_config.get("prometheus_labels", {}))
            check_prometheus_labels(service, prometheus_label_keys, service_prometheus_labels)

            for secret in service_config.get("secrets"):
                if not secret.get("recursive", False):
                    logging.debug("Monitoring %s/%s", secret.get("mount_point"), secret.get("secret_path"))
                    monitor = expirationMonitor(
                        secret.get("mount_point"),
                        secret.get("secret_path"),
                        vault_client,
                        service,
                        service_prometheus_labels,
                        prometheus_label_keys,
                        service_config.get("metadata_fieldnames", default_metadata_filenames),
                    )
                    secret_monitors.append(monitor)
                else:
                    # Query Vault for a list of all sub secrets and then interate through *that* list of secrets
                    for sub_secret in recurse_secrets(mount_point=secret.get("mount_point"), secret_path=secret.get("secret_path"), vault_client=vault_client):
                        monitor = expirationMonitor(
                            secret.get("mount_point"),
                            sub_secret,
                            vault_client,
                            service,
                            service_prometheus_labels,
                            prometheus_label_keys,
                            service_config.get("metadata_fieldnames", default_metadata_filenames),
                        )
                        secret_monitors.append(monitor)

    return secret_monitors


def recurse_secrets(mount_point: str, secret_path: str, vault_client) -> List[str]:
    keys = vault_client.secrets.kv.v2.list_secrets(mount_point=mount_point, path=secret_path)["data"]["keys"]

    secrets = []

    for key in keys:
        # Check if the key is a "directory"
        if key[-1] == "/":
            secrets += recurse_secrets(mount_point=mount_point, secret_path=f"{secret_path}/{key[:-1]}", vault_client=vault_client)
        else:
            secrets.append(f"{secret_path}/{key}")

    return secrets


def check_prometheus_labels(service, configured_label_keys, proposed_labels):
    for key in proposed_labels.keys():
        if key not in configured_label_keys:
            raise RuntimeError(f"expiration_monitoring {service} configures prometheus_labels with key {key} which is not in the globally configured prometheus labels!")
