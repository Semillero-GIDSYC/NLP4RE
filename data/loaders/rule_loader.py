import json
from models.Rule import Rule
from models.Types import TypeC

def load_rules(path: str = "data/raw/rules.json") -> list[Rule]:
    with open(path, "r") as file:
        data = json.load(file)

    rules = []
    for item in data:
        rule = Rule(
            typeC=TypeC(item["typeC"]),
            description=item["description"],
            criterion={int(k): v for k, v in item["criterion"].items()},
            source=item["source"]
        )
        rules.append(rule)

    return rules