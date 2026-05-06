import json
from testing.models.Example import Example
from testing.models.Types import TypeC

def load_examples(path: str = "data/raw/examples.json") -> list[Example]:
    with open(path, "r") as file:
        data = json.load(file)

    examples = []
    for item in data:
        example = Example(
            text=item["text"],
            tags={TypeC(k): v for k, v in item["tags"].items()},
            explanations={TypeC(k): v for k, v in item["explanations"].items()},
        )
        examples.append(example)

    return examples