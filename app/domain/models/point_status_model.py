from enum import Enum


class PointStatusModel(str, Enum):
    WITHIN_TOLERANCE = "DENTRO_DA_TOLERANCIA"
    OUTSIDE_TOLERANCE = "FORA_DA_TOLERANCIA"

    def __str__(self) -> str:
        return self.value
