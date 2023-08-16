from dataclasses import dataclass, field
from typing import List
from .link import Link
from .resource import Resource


@dataclass
class Page(Resource):
    type: str = "page"
    links: List[Link] = field(default_factory=list)
    complete: bool = False

    @staticmethod
    def load(data: dict):
        data["links"] = list(map(lambda l: Link.load(l), data["links"]))
        return Page(**data)