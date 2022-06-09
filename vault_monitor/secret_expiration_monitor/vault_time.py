"""
Wraps time handling calls to ensure consistent formatting
"""
import logging
from typing import Dict, TypeVar, Type
from datetime import datetime, timedelta, timezone

ExpirationMetadataType = TypeVar("ExpirationMetadataType", bound="ExpirationMetadata")  # pylint: disable=invalid-name


class ExpirationMetadata:
    """
    Handles updating and retrieving last renewal and expiration timestamps from custom_metadata of a secret.
    """

    def __init__(self, last_renewed_time: datetime, expiration_time: datetime, last_renewed_timestamp_fieldname: str, expiration_timestamp_fieldname: str) -> None:
        self.last_renewed_time = last_renewed_time
        self.expiration_time = expiration_time

        self.last_renewed_timestamp_fieldname = last_renewed_timestamp_fieldname
        self.expiration_timestamp_fieldname = expiration_timestamp_fieldname

    @classmethod
    def from_duration(
        cls: Type[ExpirationMetadataType],
        expiration_weeks: int,
        expiration_days: int,
        expiration_hours: int,
        expiration_minutes: int,
        expiration_seconds: int,
        last_renewed_timestamp_fieldname: str = "last_renewed_timestamp",
        expiration_timestamp_fieldname: str = "expiration_timestamp",
    ) -> ExpirationMetadataType:
        """
        Creates an instance of ExpirationMetadata from the current time for last_renewed_time and gets the expiration from duration input
        """
        last_renewed_time = datetime.now(timezone.utc)
        expiration_delta = timedelta(weeks=expiration_weeks, days=expiration_days, hours=expiration_hours, minutes=expiration_minutes, seconds=expiration_seconds)

        expiration_time = last_renewed_time + expiration_delta

        return cls(last_renewed_time, expiration_time, last_renewed_timestamp_fieldname, expiration_timestamp_fieldname)

    # Used when reading from a secret
    @classmethod
    def from_metadata(
        cls: Type[ExpirationMetadataType], metadata: dict, last_renewed_timestamp_fieldname: str = "last_renewed_timestamp", expiration_timestamp_fieldname: str = "expiration_timestamp"
    ) -> ExpirationMetadataType:
        """
        Creates an instance of ExpirationMetadata based on custom_metadata from the secret.
        """
        last_renewed_timestamp = metadata.get(last_renewed_timestamp_fieldname, None)
        expiration_timestamp = metadata.get(expiration_timestamp_fieldname, None)

        # Missing fields or malformed timestamps means we go back to the 70s, should be very obvious to the user
        try:
            last_renewed_time = cls.__get_time_from_iso_utc(last_renewed_timestamp)
        except TypeError:
            logging.error("Failed to get last_renewed_timestamp due to issues retrieving metadata for %s, setting to 1970.", last_renewed_timestamp_fieldname)
            last_renewed_time = datetime.fromtimestamp(0, tz=timezone.utc)
        except ValueError:
            logging.error("Failed to parse last_renewed_timestamp for %s, setting to 1970.", last_renewed_timestamp_fieldname)
            last_renewed_time = datetime.fromtimestamp(0, tz=timezone.utc)


        try:
            expiration_time = cls.__get_time_from_iso_utc(expiration_timestamp)
        except TypeError:
            logging.error("Failed to get expiration_timestamp due to issues retrieving metadata for %s, setting to 1970.", expiration_timestamp_fieldname)
            expiration_time = datetime.fromtimestamp(0, tz=timezone.utc)
        except ValueError:
            logging.error("Failed to parse expiration_timestamp_field for %s, setting to 1970.", expiration_timestamp_fieldname)
            expiration_time = datetime.fromtimestamp(0, tz=timezone.utc)


        return cls(last_renewed_time, expiration_time, last_renewed_timestamp_fieldname, expiration_timestamp_fieldname)

    @staticmethod
    def __get_serialized_time_utc(time_object: datetime) -> str:
        """
        Returns iso formatted time with timezone included, assumes all times are in UTC.
        """
        return time_object.isoformat() + "Z"

    @staticmethod
    def __get_time_from_iso_utc(timestamp: str) -> datetime:
        return datetime.fromisoformat(timestamp[:-1])

    def get_serialized_expiration_metadata(self) -> Dict[str, str]:
        """
        Returns a dictionary with expiration metadata provided
        """
        return {
            self.last_renewed_timestamp_fieldname: self.__get_serialized_time_utc(self.last_renewed_time),
            self.expiration_timestamp_fieldname: self.__get_serialized_time_utc(self.expiration_time),
        }

    def get_last_renewal_timestamp(self) -> float:
        """
        Gets the timestamp for the last_renewed_timestamp field
        """
        return self.last_renewed_time.timestamp()

    def get_expiration_timestamp(self) -> float:
        """
        Gets the timestamp for the expiration timestamp field
        """
        return self.expiration_time.timestamp()
