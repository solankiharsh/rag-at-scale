from src.Shared.Exceptions import InvalidSinkConnectorException
from src.SinkConnectors.ElasticsearchSink import ElasticsearchSink
from src.SinkConnectors.SinkConnector import SinkConnector
from src.SinkConnectors.SinkConnectorEnum import SinkConnectorEnum
from utils.platform_commons.logger import logger

available_sink_connectors = [enum.value for enum in list(SinkConnectorEnum)]


class SinkConnectorFactory:
    """Class that leverages the Factory pattern to get the appropriate sink connector"""

    @staticmethod
    def get_sink(sink_name: str, sink_information: dict) -> SinkConnector:
        sink_connector_name = sink_name.replace(" ", "").lower()
        sink_connector_enum = SinkConnectorEnum.as_data_connector_enum(
            sink_connector_name=sink_connector_name
        )
        logger.info(f"Sink connector enum: {sink_connector_enum}")
        logger.info(f"SinkConnectorEnum.elasticsearchsink: {SinkConnectorEnum.elasticsearch}")
        if sink_connector_enum == SinkConnectorEnum.elasticsearch:
            return ElasticsearchSink(**sink_information)
        else:
            raise InvalidSinkConnectorException(
                f"{sink_connector_name} is an invalid sink connector. "
                f"Available connectors: {available_sink_connectors}"
            )
