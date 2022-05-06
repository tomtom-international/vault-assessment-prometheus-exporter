"""
Launches the vault monitoring exporter
"""
import logging
import argparse
from time import sleep
from io import FileIO

import yaml
from prometheus_client import start_http_server

from vault_monitor.common.vault_authenticate import get_authenticated_client

import vault_monitor.expiration_monitor.create_monitors as expiration

# Disable certain things for scripts only, as over-doing the DRY-ness of them can cause them to be less useful as samples
# pylint: disable=duplicate-code,too-many-arguments,too-many-locals


def configure_and_launch(config_file: FileIO, log_level: str = "INFO") -> None:
    """
    Read configuration file, load the specified monitors, configure exporter and enter main loop.
    """
    config = yaml.safe_load(config_file)
    logging.basicConfig(level=log_level)

    # Get the hvac client, we will have to use requests some with the token it manages
    vault_config = config.get("vault", {})
    vault_client = get_authenticated_client(auth_config=vault_config.get("authentication"), address=vault_config.get("address", None), namespace=vault_config.get("namespace", None))

    monitors = []

    expiration_monitoring_config = config.get("expiration_monitoring", {})
    monitors += expiration.create_monitors(expiration_monitoring_config, vault_client)

    start_http_server(config.get("port", 9935))
    print("Running on http://localhost:9935")

    while True:
        for monitor in monitors:
            monitor.update_metrics()

        # Default to 30 seconds, configurable
        sleep(config.get("refresh_interval", 30))


def main() -> None:
    """
    Get user arguments and launch the exporter
    """
    args = handle_args()
    configure_and_launch(args.config_file, args.logging)


def handle_args() -> argparse.Namespace:
    """
    Handles arg parser, returning the args object it provides.
    """
    parser = argparse.ArgumentParser(description="Update a kv2 secret with expiration metadata.")

    parser.add_argument(
        "-l",
        "--logging",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the log level.",
    )

    parser.add_argument("--config_file", type=argparse.FileType("r", encoding="UTF-8"), default="config.yaml", help="Configuration file for the exporter.")

    return parser.parse_args()


if __name__ == "__main__":
    main()
