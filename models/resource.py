from dataclasses import dataclass, field


@dataclass
class Resource:
    protocol: str = field(default="")
    domain: str = field(default="")
    remote_url: str = field(default="")
    local_url: str = field(default="")
    content_type: str = ""
