from dataclasses import dataclass, field
from typing import List

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .link import Link


@dataclass
class Resource:
    type: str = "resource"
    protocol: str = field(default="")
    domain: str = field(default="")
    remote_url: str = field(default="")
    local_url: str = field(default="")
    content_type: str = ""
    content_encoding: str = field(default_factory=str)
    return_code: int = field(default=-1)
    links: List['Link'] = field(default_factory=list)
    complete: bool = False

    @staticmethod
    def load(data: dict):
        from .link import Link
        data["links"] = list(map(lambda l: Link.load(l), data.get("links", [])))
        return Resource(**data)
