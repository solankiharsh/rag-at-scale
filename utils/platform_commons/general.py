from datetime import datetime, timezone


# utility function to convert datetime to naive (UTC)
def convert_to_naive(dt: datetime) -> datetime:
    if dt is None:
        raise ValueError("Input datetime cannot be None")
    if dt.tzinfo is not None:
        # Convert the datetime to UTC and remove the timezone information (make it naive)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)  # noqa: UP017
    return dt
