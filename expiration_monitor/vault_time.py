"""
Wraps time handling calls to ensure consistent formatting
"""

from datetime import datetime, timedelta


class expirationMetadata():
    def __init__(self, last_renewed_time: datetime, expiration_time: datetime) -> None:
        self.last_renewed_time = last_renewed_time
        self.expiration_time = expiration_time

    @classmethod
    def fromDuration(cls, expiration_weeks, expiration_days, expiration_hours, expiration_minutes, expiration_seconds):
        """
        Sets the current time for last_renewed_time and gets the expiration from duration input
        """
        last_renewed_time = datetime.utcnow()
        expiration_delta = timedelta(weeks=expiration_weeks, days=expiration_days, hours=expiration_hours, minutes=expiration_minutes, seconds=expiration_seconds)

        expiration_time = last_renewed_time + expiration_delta

        return cls(last_renewed_time, expiration_time)


    # Used when reading from a secret
    @classmethod
    def fromMetadata(cls, metadata: dict):
        last_renewed_timestamp = metadata.get(cls.__get_last_reneweal_timestamp_fieldname(), None)
        expiration_timestamp = metadata.get(cls.__get_expiration_timestamp_fieldname(), None)

        # Missing fields means we go back to the 70s (for both dates - so well expired)
        if last_renewed_timestamp:
            last_renewed_time = cls.__get_time_from_iso_utc(last_renewed_timestamp)
        else:
            last_renewed_time = datetime.fromtimestamp(0)

        if expiration_timestamp:
            expiration_time = cls.__get_time_from_iso_utc(expiration_timestamp)
        else:
            expiration_time = datetime.fromtimestamp(0)

        return cls(last_renewed_time, expiration_time)

    # TODO: Update based on config
    @staticmethod
    def __get_last_reneweal_timestamp_fieldname():
        return "last_renewed_timestamp"

    # TODO: Update based on config
    @staticmethod
    def __get_expiration_timestamp_fieldname():
        return "expiration_timestamp"

    @staticmethod
    def __get_serialized_time_utc(time_object):
        """
        Returns iso formatted time with timezone included, assumes all times are in UTC.
        """
        return time_object.isoformat() + "Z"

    @staticmethod
    def __get_time_from_iso_utc(timestamp):
        return datetime.fromisoformat(timestamp[:-1])

    def get_serialized_expiration_metadata(self):
        """
        Returns a dictionary with expiration metadata provided
        """
        return {
            self.__get_last_reneweal_timestamp_fieldname(): self.__get_serialized_time_utc(self.last_renewed_time),
            self.__get_expiration_timestamp_fieldname(): self.__get_serialized_time_utc(self.expiration_time),
        }

    def get_last_renewal_timestamp(self):
        return self.last_renewed_time.timestamp()

    def get_expiration_timestamp(self):
        return self.expiration_time.timestamp()
