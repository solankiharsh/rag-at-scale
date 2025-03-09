from src.DataConnectors.DataConnectorEnum import DataConnectorEnum
from src.DataConnectors.S3_Connector import S3SourceConnector
from src.Shared.Exceptions import InvalidDataConnectorException
from src.Shared.source_config_schema import SourceConfigSchema

available_connectors = [enum.value for enum in list(DataConnectorEnum)]


class DataConnectorFactory:
    """Class that leverages the Factory pattern to get the appropriate data connector"""

    @staticmethod
    def get_data_connector(data_connector_name: str, connector_information: dict):
        connector_name = data_connector_name.replace(" ", "").lower()
        connector_name_enum = DataConnectorEnum.as_data_connector_enum(
            data_connector_name=connector_name
        )

        if connector_name_enum == DataConnectorEnum.s3connector:
            # Wrap connector_information into the expected config object
            config = SourceConfigSchema(name="s3connector", settings=connector_information)
            return S3SourceConnector(config=config)
        else:
            raise InvalidDataConnectorException(
                f"{connector_name} is an invalid Data Connector. "
                f"Available connectors: {available_connectors}]"
            )
