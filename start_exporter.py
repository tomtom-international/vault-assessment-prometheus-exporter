from time import sleep

import yaml
import logging
from prometheus_client import start_http_server

from common.vault_authenticate import get_vault_client_for_user
from expiration_monitor.expiration_monitor import expirationMonitor


def main():
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)

    # Get the hvac client, we will have to use requests some with the token it manages
    vault_config = config.get("vault", {})
    vault_client = get_vault_client_for_user(url=vault_config.get("address", None), namespace=vault_config.get("namespace", None))

    monitors = []

    # Needs to be put into its own function in the vem module (which should be renamed as well)
    expiration_monitoring_config = config.get("expiration_monitoring", {})
    expiration_default_prometheus_labels = expiration_monitoring_config.get("prometheus_labels", {})
    expiration_default_metadata_filenames = expiration_monitoring_config.get(
        "metadata_fieldnames", {"last_renewal_timestamp": "last_renewal_timestamp", "expiration_timestamp": "expiration_timestamp"}
    )
    expiration_monitoring_secret_configs = []
    for secret_config in expiration_monitoring_config.get("services", {}):
        for service, service_config in secret_config.items():
            # Should instantiate a class with each config
            logging.info("Configuring monitoring for service %s", service)
            print(service)
            print(service_config.get("prometheus_labels", expiration_default_prometheus_labels))
            print(service_config.get("metadata_fieldnames", expiration_default_metadata_filenames))
            for secret in service_config.get("secrets"):
                logging.debug("Monitoring %s/%s", secret.get("mount_point"), secret.get("secret_path"))
                monitor = expirationMonitor(
                    secret.get("mount_point"),
                    secret.get("secret_path"),
                    vault_client,
                    service,
                    service_config.get("prometheus_labels", expiration_default_prometheus_labels),
                    service_config.get("metadata_fieldnames", expiration_default_metadata_filenames),
                )
                monitors.append(monitor)

    start_http_server(8000)

    while True:
        for monitor in monitors:
            monitor.update_metrics()

        sleep(config.get("refresh_interval", config.get("port", 8546)))


if __name__ == "__main__":
    main()
