"""
Functions for setting up expiration monitors.
"""
import logging
from copy import deepcopy
from typing import List, Dict, Sequence

from hvac import Client as hvac_client

from vault_monitor.expiration_monitor.expiration_monitor import ExpirationMonitor
from vault_monitor.expiration_monitor.secret_expiration_monitor import SecretExpirationMonitor
from vault_monitor.expiration_monitor.entity_expiration_monitor import EntityExpirationMonitor

LOGGER = logging.getLogger("secret-monitor")


def create_monitors(config: Dict, vault_client: hvac_client) -> Sequence[ExpirationMonitor]:
    """
    Returns a list of secret monitors based on provided configuration.
    """
    default_prometheus_labels = config.get("prometheus_labels", {})
    prometheus_label_keys = list(default_prometheus_labels.keys())
    default_metadata_fieldnames = config.get("metadata_fieldnames", {"last_renewal_timestamp": "last_renewal_timestamp", "expiration_timestamp": "expiration_timestamp"})

    expiration_monitors: List[ExpirationMonitor] = []
    for service_config in config.get("services", {}):
        LOGGER.info("Configuring monitoring for service %s", service_config["name"])
        # Use deepcopy since dicts are handled by ref and tend to get overwritten otherwise
        service_prometheus_labels = deepcopy(default_prometheus_labels)
        service_prometheus_labels.update(service_config.get("prometheus_labels", {}))
        if not check_prometheus_labels(prometheus_label_keys, service_prometheus_labels):
            raise ValueError(f"expiration_monitoring {service_config['name']} configures prometheus_labels with a key(s) which is not in the globally configured prometheus labels!")
        for secret in service_config.get("secrets", []):
            secret_paths = []
            if not secret.get("recursive", False):
                secret_paths.append(secret.get("secret_path"))
            else:
                secret_paths = recurse_secrets(mount_point=secret.get("mount_point"), secret_path=secret.get("secret_path"), vault_client=vault_client)

            for secret_path in secret_paths:
                LOGGER.debug("Monitoring %s/%s", secret.get("mount_point"), secret.get("secret_path"))
                secret_monitor = SecretExpirationMonitor(
                    secret.get("mount_point"),
                    secret_path,
                    vault_client,
                    service_config["name"],
                    service_prometheus_labels,
                    service_config.get("metadata_fieldnames", default_metadata_fieldnames),
                )
                expiration_monitors.append(secret_monitor)

        for entity in service_config.get("entities", []):
            entity_monitor = EntityExpirationMonitor(
                entity.get("mount_point"),
                entity.get("entity_id"),
                entity.get("entity_name"),
                vault_client,
                service_config["name"],
                service_prometheus_labels,
                service_config.get("metadata_fieldnames", default_metadata_fieldnames),
            )
            expiration_monitors.append(entity_monitor)

    return expiration_monitors


def recurse_secrets(mount_point: str, secret_path: str, vault_client: hvac_client) -> List[str]:
    """
    Recursively return a list of secret paths to monitor
    """
    keys = vault_client.secrets.kv.v2.list_secrets(mount_point=mount_point, path=secret_path)["data"]["keys"]

    secrets = []

    for key in keys:
        # Check if the key is a "directory"
        if key[-1] == "/":
            secrets += recurse_secrets(mount_point=mount_point, secret_path=f"{secret_path}/{key[:-1]}", vault_client=vault_client)
        else:
            secrets.append(f"{secret_path}/{key}")

    return secrets


def check_prometheus_labels(configured_label_keys: List[str], proposed_labels: Dict[str, str]) -> bool:
    """
    Checks that individual service configurations do not attempt to add new keys to the Prometheus labels
    """
    for key in proposed_labels.keys():
        if key not in configured_label_keys:
            return False
    return True


def get_configuration_schema() -> Dict:
    """
    Return the configuration schema for secrets monitoring.
    """
    config_schema = {
        "expiration_monitoring": {
            "meta": {"description": "Configuration for expiration monitor module."},
            "type": "dict",
            "schema": {
                "metadata_fieldnames": {
                    "type": "dict",
                    "nullable": True,
                    "schema": {
                        "last_renewal_timestamp": {"type": "string"},
                        "expiration_timestamp": {"type": "string"},
                    },
                    "meta": {"description": "Custom fieldnames to use for reading the expiration metadata."},
                },
                "prometheus_labels": {
                    "type": "dict",
                    "nullable": True,
                    "keysrules": {"type": "string", "forbidden": ["secret_path", "mount_point", "service"]},
                    "meta": {"description": "Labels to set in the Prometheus metrics."},
                },
                "services": {
                    "type": "list",
                    "required": True,
                    "nullable": False,
                    "meta": {"description": "List of services from which secrets will be monitored"},
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "name": {"type": "string", "meta": {"description": "Name of service."}},
                            "metadata_fieldnames": {
                                "type": "dict",
                                "nullable": True,
                                "meta": {"description": "Custom fieldnames to use for reading the expiration metadata."},
                                "schema": {"last_renewal_timestamp": {"type": "string"}, "expiration_timestamp": {"type": "string"}},
                            },
                            "prometheus_labels": {
                                "type": "dict",
                                "nullable": True,
                                "dependencies": "^expiration_monitoring.prometheus_labels",
                                "keysrules": {"type": "string", "forbidden": ["secret_path", "mount_point", "service"]},
                                "meta": {"description": "Labels to set in the Prometheus metrics. All of the keys must already exist in the global prometheus_labels."},
                            },
                            "secrets": {
                                "type": "list",
                                "required": False,
                                "nullable": False,
                                "meta": {"description": "List of secrets to monitor."},
                                "schema": {
                                    "type": "dict",
                                    "schema": {
                                        "mount_point": {
                                            "type": "string",
                                            "required": True,
                                            "nullable": False,
                                            "meta": {"description": "Mount point (secret engine) secret resides in. Must be a kv2 secret engine."},
                                        },
                                        "secret_path": {"type": "string", "required": True, "nullable": False, "meta": {"description": "Path to the secret (minus the mount_point)."}},
                                        "recursive": {"type": "boolean", "nullable": False, "meta": {"description": "Recursively monitor all secrets at or below the secret_path."}},
                                    },
                                },
                            },
                            "entities": {
                                "type": "list",
                                "required": False,
                                "nullable": False,
                                "meta": {"description": "List of entities to monitor."},
                                "schema": {
                                    "type": "dict",
                                    "schema": {
                                        "mount_point": {
                                            "type": "string",
                                            "required": True,
                                            "nullable": False,
                                            "meta": {"description": "Mount point for the entities authentication type.."},
                                        },
                                        "entity_id": {"type": "string", "required": True, "nullable": False, "meta": {"description": "Entity ID for the entity to monitor."}},
                                        "entity_name": {"type": "string", "required": True, "nullable": False, "meta": {"description": "User friendly name for the entity."}},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }
    }

    return config_schema
