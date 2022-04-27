from time import sleep

import yaml
import logging
from prometheus_client import start_http_server

from common.vault_authenticate import get_vault_client_for_user
import expiration_monitor.create_monitors as expiration


def main():
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)

    # Get the hvac client, we will have to use requests some with the token it manages
    vault_config = config.get("vault", {})
    # TODO: Accept K8S and AppRole as well as built-in token
    vault_client = get_vault_client_for_user(url=vault_config.get("address", None), namespace=vault_config.get("namespace", None))

    monitors = []

    expiration_monitoring_config = config.get("expiration_monitoring", {})
    monitors += expiration.create_monitors(expiration_monitoring_config, vault_client)

    start_http_server(config.get("port", 8546))

    while True:
        for monitor in monitors:
            monitor.update_metrics()

        sleep(config.get("refresh_interval", 30))


if __name__ == "__main__":
    main()
