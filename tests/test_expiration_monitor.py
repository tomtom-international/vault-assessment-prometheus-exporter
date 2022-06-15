import pytest
from mock import call
from pytest_mock import mocker

from vault_monitor.secret_expiration_monitor import expiration_monitor

@pytest.fixture(autouse=True)
def tear_down():
    # Let test run first
    yield
    #
    delattr(expiration_monitor.ExpirationMonitor, "secret_expiration_timestamp_gauge")
    delattr(expiration_monitor.ExpirationMonitor, "secret_last_renewal_timestamp_gauge")


def test_basic_creation(mocker):
    """
    Ensure all the basic setup works
    """
    mock_vault_client = mocker.Mock()
    mock_gauge = mocker.patch.object(expiration_monitor, "Gauge", autospec=True)

    expected_labels = {"secret_path": "secret_path", "mount_point": "mount_point", "service": "service"}
    test_object = expiration_monitor.ExpirationMonitor(mount_point="mount_point", secret_path="secret_path", vault_client=mock_vault_client, service="service")

    assert test_object.prometheus_labels == expected_labels

    assert test_object.last_renewed_timestamp_fieldname == "last_renewal_timestamp"
    assert test_object.expiration_timestamp_fieldname == "expiration_timestamp"

    gauge_calls = [
        call("vault_secret_last_renewal_timestamp", "Timestamp for when a secret was last updated.", list(expected_labels.keys())),
        call("vault_secret_expiration_timestamp", "Timestamp for when a secret should expire.", list(expected_labels.keys())),
    ]

    mock_gauge.assert_has_calls(gauge_calls)
   


def test_custom_values_creation(mocker):
    """
    Set custom values for prometheus labels and metadata and ensure they are reflected in the class
    """
    mock_vault_client = mocker.Mock()
    mock_gauge = mocker.patch.object(expiration_monitor, "Gauge", autospec=True)

    expected_labels = {"secret_path": "secret_path", "mount_point": "mount_point", "service": "service", "key": "value"}
    test_object = expiration_monitor.ExpirationMonitor(
        mount_point="mount_point",
        secret_path="secret_path",
        vault_client=mock_vault_client,
        service="service",
        prometheus_labels={"key": "value"},
        metadata_fieldnames={"last_renewal_timestamp": "some_other_renewal_name", "expiration_timestamp": "some_other_expiration_name"},
    )

    assert test_object.prometheus_labels == expected_labels

    assert test_object.last_renewed_timestamp_fieldname == "some_other_renewal_name"
    assert test_object.expiration_timestamp_fieldname == "some_other_expiration_name"

    gauge_calls = [
        call("vault_secret_last_renewal_timestamp", "Timestamp for when a secret was last updated.", list(expected_labels.keys())),
        call("vault_secret_expiration_timestamp", "Timestamp for when a secret should expire.", list(expected_labels.keys())),
    ]

    mock_gauge.assert_has_calls(gauge_calls)

