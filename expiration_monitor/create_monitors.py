import logging
from typing import List, Dict

from expiration_monitor.expiration_monitor import expirationMonitor

def create_monitors(config: Dict, vault_client) -> List[expirationMonitor]:
    default_prometheus_labels = config.get("prometheus_labels", {})
    default_metadata_filenames = config.get(
        "metadata_fieldnames", {"last_renewal_timestamp": "last_renewal_timestamp", "expiration_timestamp": "expiration_timestamp"}
    )

    secret_monitors = []
    for secret_config in config.get("services", {}):
        for service, service_config in secret_config.items():
            # Should instantiate a class with each config
            logging.info("Configuring monitoring for service %s", service)
            for secret in service_config.get("secrets"):
                logging.debug("Monitoring %s/%s", secret.get("mount_point"), secret.get("secret_path"))
                monitor = expirationMonitor(
                    secret.get("mount_point"),
                    secret.get("secret_path"),
                    vault_client,
                    service,
                    service_config.get("prometheus_labels", default_prometheus_labels),
                    service_config.get("metadata_fieldnames", default_metadata_filenames),
                )
                secret_monitors.append(monitor)
    return secret_monitors