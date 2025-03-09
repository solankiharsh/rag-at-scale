from abc import ABC


class RagVector(ABC):
    def __init__(self, id: str, vector: list[float], metadata: dict) -> None:
        self.id: str = id
        self.vector: list[float] = vector
        self.metadata: dict = metadata
