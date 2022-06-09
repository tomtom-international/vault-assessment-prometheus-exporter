import datetime

import pytest
from pytest_mock import mocker

from vault_monitor.secret_expiration_monitor.vault_time import ExpirationMetadata


@pytest.mark.parametrize("weeks, days, hours, minutes, seconds", [(1, 1, 1, 2, 4), (8, 10, 1105, 20, 4444)])
def test_from_duration_get_seralized_expiration(weeks, days, hours, minutes, seconds):
    """
    Tests that creating from duration results in matching metadata
    """
    last_renewed_time = datetime.datetime.now(tz=datetime.timezone.utc)
    expiration_delta = datetime.timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
    expiration = last_renewed_time + expiration_delta
    expiration_metadata = ExpirationMetadata.from_duration(weeks, days, hours, minutes, seconds)

    metadata_dict = expiration_metadata.get_serialized_expiration_metadata()

    # Give 50 milliseconds grace period between calling utcnow here and the code calling it
    assert datetime.datetime.fromisoformat(metadata_dict["last_renewed_timestamp"][:-1]) - last_renewed_time < datetime.timedelta(milliseconds=50)
    assert datetime.datetime.fromisoformat(metadata_dict["expiration_timestamp"][:-1]) - expiration < datetime.timedelta(milliseconds=50)


def test_from_metadata_get_seralized_expiration():
    """
    Tests that creating from metadata results in matching metadata being available
    """
    metadata = {"expiration_timestamp": "2022-08-08T09:49:41.415869Z", "last_renewed_timestamp": "2022-05-02T09:49:41.415869Z"}

    expiration_metadata = ExpirationMetadata.from_metadata(metadata)
    assert expiration_metadata.get_serialized_expiration_metadata() == metadata


@pytest.mark.parametrize(
    "input, output",
    [
        # Missing last_renewed_timestamp
        (
            {
                "expiration_timestamp": "2022-08-08T09:49:41.415869Z",
            },
            {"expiration_timestamp": "2022-08-08T09:49:41.415869Z", "last_renewed_timestamp": "1970-01-01T00:00:00+00:00Z"},
        ),
        # Missing expiration_timestamp
        (
            {
                "last_renewed_timestamp": "2022-08-08T09:49:41.415869Z",
            },
            {"last_renewed_timestamp": "2022-08-08T09:49:41.415869Z", "expiration_timestamp": "1970-01-01T00:00:00+00:00Z"},
        ),
        # Timezone dropped from expiration_timestamp
        (
            {"expiration_timestamp": "2022-08-08T09:49:41.415869", "last_renewed_timestamp": "2022-05-02T09:49:41.415869Z"},
            {"expiration_timestamp": "1970-01-01T00:00:00+00:00Z", "last_renewed_timestamp": "2022-05-02T09:49:41.415869Z"},
        ),
        # Timezone dropped from last_renewed_timestamp
        (
            {"expiration_timestamp": "2022-08-08T09:49:41.415869Z", "last_renewed_timestamp": "2022-05-02T09:49:41.415869"},
            {"expiration_timestamp": "2022-08-08T09:49:41.415869Z", "last_renewed_timestamp": "1970-01-01T00:00:00+00:00Z"},
        ),
        # Malformed expiration_timestamp
        (
            {"expiration_timestamp": "2022-08-008T09:49:41.415869Z", "last_renewed_timestamp": "2022-05-02T09:49:41.415869Z"},
            {"expiration_timestamp": "1970-01-01T00:00:00+00:00Z", "last_renewed_timestamp": "2022-05-02T09:49:41.415869Z"},
        ),
        # Malformed last_renewed_timestamp
        (
            {"expiration_timestamp": "2022-08-08T09:49:41.415869Z", "last_renewed_timestamp": "2022-05-002T09:49:41.415869Z"},
            {"expiration_timestamp": "2022-08-08T09:49:41.415869Z", "last_renewed_timestamp": "1970-01-01T00:00:00+00:00Z"},
        ),
        # Missing both
        (
            {},
            {"expiration_timestamp": "1970-01-01T00:00:00+00:00Z", "last_renewed_timestamp": "1970-01-01T00:00:00+00:00Z"},
        ),
        # Malformed both
        (
            {"expiration_timestamp": "2022-008-08T09:49:41.415869Z", "last_renewed_timestamp": "2022-05-002T09:49:41.415869Z"},
            {"expiration_timestamp": "1970-01-01T00:00:00+00:00Z", "last_renewed_timestamp": "1970-01-01T00:00:00+00:00Z"},
        ),
    ],
)
def test_missing_fieldname_and_malformed_timestamp_is_zero(input, output):
    """
    Tests that missing or malformed timestamps get set to zero (the beginning of the Unix epoch)
    """
    expiration_metadata_object = ExpirationMetadata.from_metadata(input)
    assert expiration_metadata_object.get_serialized_expiration_metadata() == output
