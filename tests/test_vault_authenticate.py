import pytest
import os
import mock
import hvac
from pytest_mock import mocker
from mock import call

import vault_monitor.common.vault_authenticate


def test_vault_client_for_user_success(mocker):
    test_token = "testtoken1234"
    test_url = "https://vault.test.url"
    test_namespace = "testnamespace"

    assert isinstance(vault_monitor.common.vault_authenticate.get_vault_client_for_user(url=test_url, namespace=test_namespace, vault_token=test_token), hvac.Client)


@mock.patch.dict(os.environ, {"VAULT_ADDR": ""})
def test_vault_client_for_user_url_runtime():
    test_namespace = "testnamespace"
    test_token = "testtoken1234"
    test_url = None

    with pytest.raises(RuntimeError):
        vault_monitor.common.vault_authenticate.get_vault_client_for_user(url=test_url, namespace=test_namespace, vault_token=test_token)


@mock.patch("builtins.open", mock.mock_open(read_data=""))
def test_vault_client_for_user_token_runtime():
    test_namespace = "testnamespace"
    test_url = "https://test.vault.url"

    with pytest.raises(RuntimeError):
        vault_monitor.common.vault_authenticate.get_vault_client_for_user(url=test_url, namespace=test_namespace)


def test_get_authenticated_client_approle(mocker):
    test_namespace = "test_namespace"
    test_address = "https://vault.test.addr"
    test_config = {"approle": {"mount_point": "approle", "role_id": "role_id_test_1234", "secret_id": "secret_id_test_1234"}}

    mock_get_namespace = mocker.patch("vault_monitor.common.vault_authenticate.get_namespace", return_value=test_namespace)
    mock_get_address = mocker.patch("vault_monitor.common.vault_authenticate.get_address", return_value=test_address)

    mock_client = mocker.Mock()
    mock_return_approle_client = mocker.patch("vault_monitor.common.vault_authenticate.get_client_with_approle_auth", return_value=mock_client)

    vault_monitor.common.vault_authenticate.get_authenticated_client(test_config, test_address, test_namespace)

    mock_get_namespace.assert_called_once_with(test_namespace)
    mock_get_address.assert_called_once_with(test_address)
    mock_return_approle_client.assert_called_once_with(test_config.get("approle"), test_address, test_namespace)


@mock.patch("builtins.open", mock.mock_open(read_data="test_kubernetes_token"))
def test_get_authenticated_client_kubernetes(mocker):
    test_namespace = "test_namespace"
    test_address = "https://vault.test.addr"
    test_config = {"kubernetes": "token_file_path"}

    mock_get_namespace = mocker.patch("vault_monitor.common.vault_authenticate.get_namespace", return_value=test_namespace)
    mock_get_address = mocker.patch("vault_monitor.common.vault_authenticate.get_address", return_value=test_address)

    mock_client = mocker.Mock()
    mock_return_approle_client = mocker.patch("vault_monitor.common.vault_authenticate.get_client_with_kubernetes_auth", return_value=mock_client)

    vault_monitor.common.vault_authenticate.get_authenticated_client(test_config, test_address, test_namespace)

    mock_get_namespace.assert_called_once_with(test_namespace)
    mock_get_address.assert_called_once_with(test_address)
    mock_return_approle_client.assert_called_once_with(test_config.get("kubernetes"), test_address, test_namespace)


@mock.patch("builtins.open", mock.mock_open(read_data="test_token"))
def test_get_authenticated_client_token(mocker):
    test_namespace = "test_namespace"
    test_address = "https://vault.test.addr"
    test_config = {"token": "token_file_path"}

    mock_get_namespace = mocker.patch("vault_monitor.common.vault_authenticate.get_namespace", return_value=test_namespace)
    mock_get_address = mocker.patch("vault_monitor.common.vault_authenticate.get_address", return_value=test_address)

    mock_client = mocker.Mock()
    mock_return_approle_client = mocker.patch("vault_monitor.common.vault_authenticate.get_client_with_token_auth", return_value=mock_client)

    vault_monitor.common.vault_authenticate.get_authenticated_client(test_config, test_address, test_namespace)

    mock_get_namespace.assert_called_once_with(test_namespace)
    mock_get_address.assert_called_once_with(test_address)
    mock_return_approle_client.assert_called_once_with(test_config.get("token"), test_address, test_namespace)


@mock.patch.dict(os.environ, {"VAULT_NAMESPACE": "testnamespace"})
def test_get_namespace(mocker):
    test_namespace = "testnamespace"
    assert vault_monitor.common.vault_authenticate.get_namespace() == test_namespace


@mock.patch.dict(os.environ, {"VAULT_ADDR": "https://test.vault.addr"})
def test_get_address(mocker):
    test_address = "https://test.vault.addr"
    assert vault_monitor.common.vault_authenticate.get_address() == test_address


@mock.patch("builtins.open", mock.mock_open(read_data="asdf-1243"))
@mock.patch.dict(os.environ, {"ROLE_ID": "1243-asdf"})
def test_get_client_with_approle_auth_creds_in_file(mocker):
    test_config = {
        "mount_point": "approle",
        "role_id_variable": "ROLE_ID",
        "secret_id_file": "secret_file",
    }
    test_address = "https://vault.test.addr"
    test_namespace = "testnamespace"

    mock_client = mocker.Mock()
    mock_get_client = mocker.patch("vault_monitor.common.vault_authenticate.hvac.Client", return_value=mock_client)

    vault_monitor.common.vault_authenticate.get_client_with_approle_auth(config=test_config, address=test_address, namespace=test_namespace)

    mock_get_client.assert_called_once_with(url=test_address, namespace=test_namespace)
    mock_client.auth.approle.login.assert_called_once_with(role_id="1243-asdf", secret_id="asdf-1243", mount_point="approle")


@mock.patch("builtins.open", mock.mock_open(read_data="1243-asdf"))
@mock.patch.dict(os.environ, {"SECRET_ID": "asdf-1243"})
def test_get_client_with_approle_auth_creds_in_env(mocker):
    test_config = {
        "mount_point": "approle",
        "role_id_file": "role_file",
        "secret_id_variable": "SECRET_ID",
    }
    test_address = "https://vault.test.addr"
    test_namespace = "testnamespace"

    mock_client = mocker.Mock()
    mock_get_client = mocker.patch("vault_monitor.common.vault_authenticate.hvac.Client", return_value=mock_client)

    vault_monitor.common.vault_authenticate.get_client_with_approle_auth(config=test_config, address=test_address, namespace=test_namespace)

    mock_get_client.assert_called_once_with(url=test_address, namespace=test_namespace)
    mock_client.auth.approle.login.assert_called_once_with(role_id="1243-asdf", secret_id="asdf-1243", mount_point="approle")


def test_get_client_with_approle_auth_creds_in_config(mocker):
    test_config = {
        "mount_point": "approle",
        "role_id": "1243-asdf",
        "secret_id": "asdf-1243",
    }
    test_address = "https://vault.test.addr"
    test_namespace = "testnamespace"

    mock_client = mocker.Mock()
    mock_get_client = mocker.patch("vault_monitor.common.vault_authenticate.hvac.Client", return_value=mock_client)

    vault_monitor.common.vault_authenticate.get_client_with_approle_auth(config=test_config, address=test_address, namespace=test_namespace)

    mock_get_client.assert_called_once_with(url=test_address, namespace=test_namespace)
    mock_client.auth.approle.login.assert_called_once_with(role_id="1243-asdf", secret_id="asdf-1243", mount_point="approle")


@mock.patch("builtins.open", mock.mock_open(read_data="test_kubernetes_token"))
def test_get_client_with_kubernetes_auth(mocker):
    test_config = {"mount_point": "kubernetes", "token_file": "/var/run/secrets/kubernetes.io/serviceaccount/token"}
    test_namespace = "testnamespace"
    test_address = "https://vault.test.addr"

    mock_client = mocker.Mock()
    mock_get_client = mocker.patch("vault_monitor.common.vault_authenticate.hvac.Client", return_value=mock_client)  # check it's getting called with line 120 (original)

    vault_monitor.common.vault_authenticate.get_client_with_kubernetes_auth(config=test_config, address=test_address, namespace=test_namespace)

    mock_get_client.assert_called_once_with(url=test_address, namespace=test_namespace)
    mock_client.auth_kubernetes.assert_called_once_with("kubernetes", "test_kubernetes_token")


@mock.patch.dict(os.environ, {"VAULT_TOKEN": "test_token"})
def test_get_client_with_token_auth_var_success():
    test_config = {"token_var_name": "VAULT_TOKEN"}
    test_address = "https://test.vault.addr"
    test_namespace = "testnamespace"

    assert isinstance(vault_monitor.common.vault_authenticate.get_client_with_token_auth(config=test_config, address=test_address, namespace=test_namespace), hvac.Client)


@mock.patch("builtins.open", mock.mock_open(read_data="test_token"))
def test_get_client_with_token_auth_file_success():
    test_config = {"token_file": "~/.vault-token"}
    test_address = "https://test.vault.addr"
    test_namespace = "testnamespace"

    assert isinstance(vault_monitor.common.vault_authenticate.get_client_with_token_auth(config=test_config, address=test_address, namespace=test_namespace), hvac.Client)
