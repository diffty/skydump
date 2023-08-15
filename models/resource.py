from dataclasses import dataclass, field


@dataclass
class Resource:
    type: str = "resource"
    protocol: str = field(default="")
    domain: str = field(default="")
    remote_url: str = field(default="")
    local_url: str = field(default="")
    content_type: str = ""

    @staticmethod
    def load(data: dict):
        return Resource(**data)