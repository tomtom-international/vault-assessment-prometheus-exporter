"""
Functions for getting Hashicorp Vault client
"""
import os
import logging

import hvac

LOGGER = logging.getLogger("vault_authenticate")


def get_vault_client_for_user(url: str = None, namespace: str = None, vault_token: str = None) -> hvac.Client:
    """
    Gets a HVAC Vault client instance configured against Vault, targeted towards end-user systems (checks for environmental variables and existing token in .vault-token)
    """
    if not url:
        url = os.getenv("VAULT_ADDR")
    if not namespace:
        namespace = os.getenv("VAULT_NAMESPACE")
    if not vault_token:
        LOGGER.debug("Attempting to read Vault token from file.")
        with open(os.path.expanduser("~/.vault-token"), "r", encoding="utf8") as token_file:
            vault_token = token_file.read()

    # If the values still aren't set, raise an error or warn user as appropriate
    if not url:
        raise RuntimeError("Unable to get Vault URL.\nPlease provide it as an argument or set the VAULT_ADDR environmental variable.")
    if not namespace:
        LOGGER.info("No namespace provided, so using root namespace.")
    if not vault_token:
        raise RuntimeError("Unable to get Vault token.\nPlease execute `vault login`, provide it as an argument or set the VAULT_ADDR environmental variable.")

    return hvac.Client(url=url, token=vault_token, namespace=namespace)
