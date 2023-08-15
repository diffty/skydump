from dataclasses import dataclass, field
from typing import List
from .link import Link
from .resource import Resource


@dataclass
class Page(Resource):
    links: List[Link] = field(default_factory=list)
