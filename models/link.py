from dataclasses import dataclass, field
from .resource import Resource


@dataclass
class Link:
    origin: str = field(default="")
    original_url: str = field(default="")
    resource: Resource = field(default=None)
