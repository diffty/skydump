from dataclasses import dataclass, asdict, field
from typing import List
from .link import Link


@dataclass
class Page:
    domain: str = field(default="")
    remote_url: str = field(default="")
    local_url: str = field(default="")
    links: List[Link] = field(default_factory=list)
