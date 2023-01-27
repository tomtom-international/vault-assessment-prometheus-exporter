"""
Functions for getting Hashicorp Vault client
"""
import os
import logging
import warnings

from typing import Optional, Dict

import hvac

LOGGER = logging.getLogger("vault_authenticate")


def get_vault_client_for_user(url: Optional[str] = None, namespace: Optional[str] = None, vault_token: Optional[str] = None) -> hvac.Client:
    """
    Gets a HVAC Vault client instance configured against Vault, targeted towards end-user systems (checks for environmental variables and existing token in .vault-token)
    """
    url = get_address(url)
    namespace = get_namespace(namespace)
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


def get_authenticated_client(auth_config: Dict[str, Dict[str, str]], address: str, namespace: str) -> hvac.Client:
    """
    Returns an authenticated Vault client as configured by the authentication section of the configuration file.
    """
    namespace = get_namespace(namespace)
    address = get_address(address)

    if len(auth_config) > 1:
        warnings.warn("Multiple authentication methods are selected. Only the highest priority one will be used, please review your configuration!")

    approle_auth_config = auth_config.get("approle", None)
    kubernetes_auth_config = auth_config.get("kubernetes", None)
    token_auth_config = auth_config.get("token", {})

    if approle_auth_config is not None:
        return get_client_with_approle_auth(approle_auth_config, address, namespace)

    if kubernetes_auth_config is not None:
        return get_client_with_kubernetes_auth(kubernetes_auth_config, address, namespace)

    # As a last ditch effort check for tokens, this includes checking for sensible defaults in case of limited configuration
    if token_auth_config is None:
        token_auth_config = {}
    return get_client_with_token_auth(token_auth_config, address, namespace)


def get_namespace(namespace: Optional[str] = None) -> str:
    """
    In the event that namespace is None, return the value for VAULT_NAMESPACE if that is set
    """
    # Checks explicitly for None, an empty string is a valid option
    if namespace is None:
        namespace = str(os.getenv("VAULT_NAMESPACE", ""))
    return namespace


def get_address(address: Optional[str] = None) -> str:
    """
    If the Vault address isn't set, check the contents of the VAULT_ADDR environmental variable and return it.
    """
    if not address:
        address = str(os.getenv("VAULT_ADDR", ""))
    return address


def get_client_with_approle_auth(config: Dict[str, str], address: str, namespace: str) -> hvac.Client:
    """
    Returns an authenticated Vault client with approle authentication.
    """
    mount_point = config.get("mount_point", "approle")
    role_id = config.get("role_id", None)
    if not role_id:
        role_id_variable = config.get("role_id_variable", None)
        if role_id_variable:
            role_id = os.getenv(role_id_variable)
        else:
            role_id_filename = config.get("role_id_file", None)
            if role_id_filename:
                with open(role_id_filename, "r", encoding="UTF8") as role_id_file:
                    role_id = role_id_file.read()

    secret_id = config.get("secret_id", None)
    if not secret_id:
        secret_id_variable = config.get("secret_id_variable", None)
        if secret_id_variable:
            secret_id = os.getenv(secret_id_variable)
        else:
            secret_id_filename = config.get("secret_id_file", None)
            if secret_id_filename:
                with open(secret_id_filename, "r", encoding="UTF8") as secret_id_file:
                    secret_id = secret_id_file.read()

    client = hvac.Client(url=address, namespace=namespace)
    client.auth.approle.login(role_id=role_id, secret_id=secret_id, mount_point=mount_point)
    return client


def get_client_with_kubernetes_auth(config: Dict[str, str], address: str, namespace: str) -> hvac.Client:
    """
    Returns an authenticated Vault client with Kuberenetes authentication.
    """
    mount_point = config.get("mount_point", "kubernetes")
    role = config.get("role", "vape")
    jwt_file_path = config.get("token_file", "/var/run/secrets/kubernetes.io/serviceaccount/token")
    with open(jwt_file_path, "r", encoding="UTF8") as jwt_file:
        jwt = jwt_file.read()
    client = hvac.Client(url=address, namespace=namespace)
    client.auth.kubernetes.login(role, jwt, mount_point=mount_point)
    return client


def get_client_with_token_auth(config: Dict[str, str], address: str, namespace: str) -> hvac.Client:
    """
    Returns an authenticated Vault client using token authentication.
    """
    token_var_name = config.get("token_var_name", None)
    token_filename = config.get("token_file", None)
    vault_token = None
    if token_var_name:
        vault_token = os.getenv(token_var_name, None)
    elif token_filename:
        with open(os.path.expanduser(token_filename), "r", encoding="utf8") as token_file:
            vault_token = token_file.read()

    # If vault_token is none, the hvac client will check for sensible defaults during init (VAULT_TOKEN and ~/.vault-token)
    return hvac.Client(url=address, token=vault_token, namespace=namespace)
