from enum import Enum
from dataclasses import dataclass


class LinkType(Enum):
    UNKNOWN = 0
    PAGE = 1
    RESOURCE = 2


@dataclass
class Link:
    type: LinkType = LinkType.UNKNOWN
    remote_url: str = ""
    local_url: str = ""
    original_url: str = ""
    content_type: str = ""
    origin: str = ""
    ignored: bool = False