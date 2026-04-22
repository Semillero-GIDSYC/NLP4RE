from models.Types import TypeC
from dataclasses import dataclass

@dataclass
class Rule():
    typeC: TypeC
    description: str
    criterion: dict[int, str]
    source: str
     
