"""
Launches Vault Assessment Prometheus Exporter
"""
import sys
import logging
import argparse
from time import sleep
from io import FileIO
from typing import Dict, List, Any

import yaml
from prometheus_client import start_http_server
from cerberus import Validator

from vault_monitor.common.vault_authenticate import get_authenticated_client

import vault_monitor.secret_expiration_monitor.create_monitors as expiration

EXPORTER_MODULES = [expiration]

# Disable certain things for scripts only, as over-doing the DRY-ness of them can cause them to be less useful as samples
# pylint: disable=duplicate-code,too-many-arguments,too-many-locals


def configure_and_launch(config_file: FileIO, log_level: str = "INFO") -> None:
    """
    Read configuration file, load the specified monitors, configure exporter and enter main loop.
    """
    config = yaml.safe_load(config_file)
    logging.basicConfig(level=log_level)

    # Validation
    config_schema = get_config_schema(modules=EXPORTER_MODULES)
    config_validator = Validator(config_schema)
    config_validator.allow_unknown = False
    if not config_validator.validate(config):
        raise ValueError(config_validator.errors)

    # Get the hvac client, we will have to use requests some with the token it manages
    vault_config = config.get("vault", {})
    vault_client = get_authenticated_client(auth_config=vault_config.get("authentication"), address=vault_config.get("address", None), namespace=vault_config.get("namespace", None))

    monitors = []

    secret_expiration_monitoring_config = config.get("secret_expiration_monitoring", {})
    monitors += expiration.create_monitors(secret_expiration_monitoring_config, vault_client)

    refresh_interval = config.get("refresh_interval", 30)
    port = config.get("port", 9935)

    start_http_server(port)
    print(f"Running on http://localhost:{port}")

    while True:
        for monitor in monitors:
            monitor.update_metrics()

        # Default to 30 seconds, configurable
        sleep(refresh_interval)


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

    parser.add_argument("--show_schema", action=PrintSchema, help="Set to print config schema and exit.")

    return parser.parse_args()


class PrintSchema(argparse.Action):  # pylint: disable=too-few-public-methods
    """
    Custom argparse action to print the configuration schema.
    """

    def __init__(self, *args: Any, nargs: int = 0, **kwargs: Any) -> None:
        kwargs["nargs"] = nargs
        super().__init__(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        class NoAliasDumper(yaml.Dumper):  # pylint: disable=too-many-ancestors
            """
            Incline class to allow dumping the schema without aliases
            """

            def ignore_aliases(self, data: Dict) -> bool:
                """
                Allow ignoring aliases
                """
                return True

        schema = get_config_schema(EXPORTER_MODULES)
        print(yaml.dump(schema, Dumper=NoAliasDumper))
        sys.exit(0)


def get_approle_valid_combinations() -> List[Dict[str, Dict[str, str]]]:
    """
    Gets valid combinations for the approle authentication type, rather than listing out all combinations manually.
    """
    role_id_values = ["role_id", "role_id_variable", "role_id_file"]
    secret_id_values = ["secret_id", "secret_id_variable", "secret_id_file"]

    combos = []

    rules = {"type": "string"}

    for role_id_value in role_id_values:
        for secret_id_value in secret_id_values:
            combo = {role_id_value: rules, secret_id_value: rules, "mount_point": rules}
            combos.append(combo)

    return combos


def get_config_schema(modules: List) -> Dict[str, Dict]:
    """
    Gets the configuration schema, including update it with any provided by modules.
    """
    schema: Dict[str, Dict]
    schema = {
        "vault": {
            "type": "dict",
            "nullable": False,
            "required": True,
            "meta": {"description": "Configuration for connecting to HashiCorp Vault."},
            "schema": {
                "address": {
                    "type": "string",
                    "nullable": True,
                    "regex": "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                    "meta": {"description": "Address of Vault to connect to (including schema)."},
                },
                "namespace": {"type": "string", "nullable": True, "meta": {"description": "Namespace to connect, leave blank for root namespace/Open Source Vault."}},
                "authentication": {
                    "type": "dict",
                    "nullable": False,
                    "required": True,
                    "oneof_schema": [
                        {
                            "token": {
                                "type": "dict",
                                "schema": {
                                    "token_var_name": {"type": "string", "nullable": True},
                                    "token_file": {"type": "string", "nullable": True},
                                },
                                "meta": {"description": "Token authentication configuration.", "link": "https://www.vaultproject.io/docs/auth/token"},
                            }
                        },
                        {
                            "kubernetes": {
                                "type": "dict",
                                "schema": {
                                    "token_file": {"type": "string"},
                                    "mount_point": {"type": "string"},
                                },
                                "meta": {"description": "Configuration for Kubernetes authentication method.", "link": "https://www.vaultproject.io/docs/auth/kubernetes"},
                            }
                        },
                        {"approle": {"type": "dict", "meta": {"description": "Configuration for AppRole authentication method.", "link": "https://www.vaultproject.io/docs/auth/approle"}}},
                    ],
                    "meta": {"description": "Authentication type to connect with."},
                },
            },
        },
        "refresh_interval": {"type": "integer", "nullable": True, "meta": {"description": "Frequency in seconds with which the exporter should connect to Vault and read the metadata information."}},
        "port": {"type": "integer", "nullable": True, "min": 1, "max": 65535, "meta": {"description": "Port number to run exporter on."}},
    }

    schema["vault"]["schema"]["authentication"]["oneof_schema"][2]["approle"]["oneof_schema"] = get_approle_valid_combinations()

    for module in modules:
        schema.update(module.get_configuration_schema())

    return schema


if __name__ == "__main__":
    main()
