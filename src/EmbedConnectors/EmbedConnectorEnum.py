from enum import Enum


class EmbedConnectorEnum(str, Enum):
    jina_v2_base = "jina-v2-base"
    thinktankembed = "thinktankembed"
    openaiembed = "openaiembed"

    def as_embed_connector_enum(embed_connector_name: str):
        if not embed_connector_name:
            return None
        try:
            normalized_name = embed_connector_name.lower().replace("-", "_")
            enum_to_return = EmbedConnectorEnum[normalized_name]
            return enum_to_return
        except KeyError:
            return None
