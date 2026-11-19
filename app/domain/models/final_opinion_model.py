from enum import Enum


class FinalOpinionModel(str, Enum):
    APPROVED = "APROVADO"
    REJECTED = "REPROVADO"

    def __str__(self) -> str:
        return self.value
