import pytest
from mock import call
from pytest_mock import mocker

from vault_monitor.expiration_monitor import entity_expiration_monitor, expiration_monitor


@pytest.fixture(autouse=True)
def tear_down():
    """
    Cleans out the mock gauges with every run
    """
    yield
    delattr(entity_expiration_monitor.EntityExpirationMonitor, "secret_last_renewal_timestamp_gauge")
    delattr(entity_expiration_monitor.EntityExpirationMonitor, "secret_expiration_timestamp_gauge")


def test_basic_creation(mocker):
    """
    Ensure all the basic setup works
    """
    mock_vault_client = mocker.Mock()
    mock_gauge = mocker.patch.object(expiration_monitor, "Gauge", autospec=True)

    expected_labels = {"monitored_path": "monitored_path", "mount_point": "mount_point", "service": "service",  "entity_name": "entity_name"}
    test_object = entity_expiration_monitor.EntityExpirationMonitor(mount_point="mount_point", monitored_path="monitored_path", name="entity_name", vault_client=mock_vault_client, service="service")

    assert test_object.prometheus_labels == expected_labels

    assert test_object.last_renewed_timestamp_fieldname == "last_renewal_timestamp"
    assert test_object.expiration_timestamp_fieldname == "expiration_timestamp"

    gauge_calls = [
        call("vault_entity_last_renewal_timestamp", "Timestamp for when an entity's secrets were last updated.", list(expected_labels.keys())),
        call("vault_entity_expiration_timestamp", "Timestamp for when an entity's secrets should be expired and rotated.", list(expected_labels.keys())),
    ]

    mock_gauge.assert_has_calls(gauge_calls)


def test_custom_values_creation(mocker):
    """
    Set custom values for prometheus labels and metadata and ensure they are reflected in the class
    """
    mock_vault_client = mocker.Mock()
    mock_gauge = mocker.patch.object(expiration_monitor, "Gauge", autospec=True)

    expected_labels = {"monitored_path": "monitored_path", "mount_point": "mount_point", "service": "service", "key": "value", "entity_name": "entity_name"}
    test_object = entity_expiration_monitor.EntityExpirationMonitor(
        mount_point="mount_point",
        monitored_path="monitored_path",
        name="entity_name",
        vault_client=mock_vault_client,
        service="service",
        prometheus_labels={"key": "value"},
        metadata_fieldnames={"last_renewal_timestamp": "some_other_renewal_name", "expiration_timestamp": "some_other_expiration_name"},
    )

    assert test_object.prometheus_labels == expected_labels

    assert test_object.last_renewed_timestamp_fieldname == "some_other_renewal_name"
    assert test_object.expiration_timestamp_fieldname == "some_other_expiration_name"

    gauge_calls = [
        call("vault_entity_last_renewal_timestamp", "Timestamp for when an entity's secrets were last updated.", list(expected_labels.keys())),
        call("vault_entity_expiration_timestamp", "Timestamp for when an entity's secrets should be expired and rotated.", list(expected_labels.keys())),
    ]

    mock_gauge.assert_has_calls(gauge_calls)
