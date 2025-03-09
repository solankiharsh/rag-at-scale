from enum import Enum


class DataConnectorEnum(str, Enum):
    s3connector = "s3connector"

    def as_data_connector_enum(data_connector_name: str):
        if data_connector_name is None or data_connector_name == "":
            return None
        try:
            enum_to_return = DataConnectorEnum[data_connector_name.lower()]
            return enum_to_return
        except KeyError:
            return None
