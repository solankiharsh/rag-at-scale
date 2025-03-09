from enum import Enum


class SinkConnectorEnum(str, Enum):
    elasticsearch = "elasticsearch"
    
    def as_data_connector_enum(sink_connector_name: str):
        if sink_connector_name == None or sink_connector_name == "":
            return None
        try:
            enum_to_return = SinkConnectorEnum[sink_connector_name.lower()]
            return enum_to_return
        except KeyError as e:
            return None