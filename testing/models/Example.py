from dataclasses import dataclass
from testing.models.Types import TypeC

@dataclass
class Example():
    text: str
    tags: dict[TypeC, int]
    explanations: dict[TypeC, str]

    @property
    def score(self) -> int:
        return sum(self.tags.values())

