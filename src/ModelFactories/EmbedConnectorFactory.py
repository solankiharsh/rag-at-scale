from src.EmbedConnectors import EmbedConnector
from src.EmbedConnectors.EmbedConnectorEnum import EmbedConnectorEnum
from src.EmbedConnectors.HamEmbedModel import HamEmbedModel
from src.EmbedConnectors.OpenAIEmbedModel import OpenAIEmbedModel
from src.EmbedConnectors.ThinkTankEmbedModel import ThinkTankEmbedModel
from src.Shared.Exceptions import InvalidEmbedConnectorException

available_embed_connectors = [enum.value for enum in list(EmbedConnectorEnum)]


class EmbedConnectorFactory:
    """Class that leverages the Factory pattern to get the appropriate embed connector"""

    @staticmethod
    def get_embed(embed_name: str, embed_information: dict) -> EmbedConnector:
        embed_connector_name = embed_name.replace(" ", "").lower()
        embed_connector_enum = EmbedConnectorEnum.as_embed_connector_enum(
            embed_connector_name=embed_connector_name
        )
        if embed_connector_enum == EmbedConnectorEnum.jina_v2_base:
            return HamEmbedModel(**embed_information)
        elif embed_connector_enum == EmbedConnectorEnum.openaiembed:
            return OpenAIEmbedModel(**embed_information)
        elif embed_connector_enum == EmbedConnectorEnum.thinktankembed:
            return ThinkTankEmbedModel(**embed_information)
        else:
            raise InvalidEmbedConnectorException(
                f"{embed_connector_name} is an invalid embed connector. "
                f"Available connectors: {available_embed_connectors}] "
            )
