"""
Updates the last-updated and expiration date-time fields for a given secret
"""

import logging
import argparse
import warnings

import requests

from common.vault_authenticate import get_vault_client_for_user
from vault_time import expirationMetadata

LOGGER = logging.getLogger("set_expiration")


def handle_args():
    parser = argparse.ArgumentParser(description="Update a kv2 secret with expiration metadata.")

    parser.add_argument("mount_point", type=str, help="Mount point of kv2 engine, e.g. secret")
    parser.add_argument("secret_path", type=str, help="Path to secret, e.g. some/secret")

    parser.add_argument(
        "-l",
        "--logging",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the log level.",
    )

    vault_group = parser.add_argument_group(title="Vault configuration")
    vault_group.add_argument("--address", type=str, default=None, help="Sets the Vault address (defaults to checking $VAULT_ADDR).")
    vault_group.add_argument("--namespace", type=str, default=None, help="Sets the Vault namespace (defaults to checking $VAULT_NAMESPACE).")

    expiration_group = parser.add_argument_group(title="Expiration time", description="Configure the amount of time until expiration.")
    expiration_group.add_argument("--weeks", default=0, type=int, help="Set the number of weeks before expiration.")
    expiration_group.add_argument("--days", default=0, type=int, help="Set the number of days before expiration.")
    expiration_group.add_argument("--hours", default=0, type=int, help="Set the number of hours before expiration.")
    expiration_group.add_argument("--minutes", default=0, type=int, help="Set the number of minutes before expiration.")
    expiration_group.add_argument("--seconds", default=0, type=int, help="Set the number of minutes before expiration.")

    fieldnames_group = parser.add_argument_group(
        title="Fieldnames", description="Configure the fieldnames to use (optional).\nThese must be matched by the exporter configuration for expiration monitoring."
    )
    fieldnames_group.add_argument("--last_renewed_timestamp_fieldname", default="last_renewal_timestamp", type=str, help="Set the fieldname to use for the last renewed timestamp.")
    fieldnames_group.add_argument("--expiration_timestamp_fieldname", default="expiration_timestamp", type=str, help="Set the fieldname to use for the expiration timestamp.")

    return parser.parse_args()


def main():
    args = handle_args()

    # Get the hvac client, we will have to use requests some with the token it manages
    vault_client = get_vault_client_for_user(url=args.address, namespace=args.namespace)

    expiration_info = expirationMetadata.fromDuration(args.weeks, args.days, args.hours, args.minutes, args.seconds, args.last_renewed_timestamp_fieldname, args.expiration_timestamp_fieldname)

    logging.basicConfig(level=args.logging)

    LOGGER.info("Updating expiration data for secret.")

    # Custom metadata isn't fully supported by hvac at the moment, use requests
    response = requests.patch(
        f"{vault_client.url}/v1/{args.mount_point}/metadata/{args.secret_path}",
        headers={"X-Vault-Namespace": vault_client.adapter.namespace, "X-Vault-Token": vault_client.token, "Content-Type": "application/merge-patch+json"},
        json={"custom_metadata": expiration_info.get_serialized_expiration_metadata()},
    )

    if response.status_code == 405:
        warnings.warn(
            "Received 405 error when attempting to PATCH metadata, GET/PUT metadata update. This indicates an older version of Vault is in us (<10), support will eventually be dropped from this tool.",
            DeprecationWarning,
        )
        response = requests.get(
            f"{vault_client.url}/v1/{args.mount_point}/metadata/{args.secret_path}",
            headers={"X-Vault-Namespace": vault_client.adapter.namespace, "X-Vault-Token": vault_client.token, "Content-Type": "application/merge-patch+json"},
        )
        response.raise_for_status()

        # Take the existing metadata, clean up what we don't control, update it and then push it
        metadata = response.json()

        # When no custom_metadata is set, Vault will return None, so we have to set up an empty dictionary
        if not metadata["data"]["custom_metadata"]:
            metadata["data"]["custom_metadata"] = {}

        metadata["data"]["custom_metadata"].update(expiration_info.get_serialized_expiration_metadata())
        metadata = metadata["data"]
        del metadata["created_time"]
        del metadata["current_version"]
        del metadata["oldest_version"]
        del metadata["updated_time"]
        del metadata["versions"]

        response = requests.put(
            f"{vault_client.url}/v1/{args.mount_point}/metadata/{args.secret_path}",
            headers={"X-Vault-Namespace": vault_client.adapter.namespace, "X-Vault-Token": vault_client.token},
            json=metadata,
        )

    response.raise_for_status()


if __name__ == "__main__":
    main()
