from abc import ABC

from src.Shared.Exceptions import RagDocumentEmptyException


class RagDocument(ABC):
    def __init__(self, id:str, content:str, metadata:dict) -> None:
        self.id:str = id
        self.content:str = content
        self.metadata:dict = metadata
    
    @classmethod
    def as_file(cls, dct:dict):
        if dct is None:
            raise RagDocumentEmptyException("Received empty dict when converting to as_file")
        return cls(id=dct.get('id'), content=dct.get('content'), metadata=dct.get('metadata'))
    
    def to_json(self):
        """Python does not have built-in serialization.
        We need this logic to be able to respond in our API..

        Returns:
            _type_: the json to return
        """
        json_to_return = {}
        json_to_return['content'] = self.content
        json_to_return['metadata'] = self.metadata
        json_to_return['id'] = self.id
        return json_to_return
    