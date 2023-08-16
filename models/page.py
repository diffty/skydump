from dataclasses import dataclass, field
from typing import List
from .link import Link
from .resource import Resource


@dataclass
class Page(Resource):
    type: str = "page"
    complete: bool = False

    @staticmethod
    def load(data: dict):
        data["links"] = list(map(lambda l: Link.load(l), data.get("links", [])))
        return Page(**data)
