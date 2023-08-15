from dataclasses import dataclass, field
from .resource import Resource


@dataclass
class Link:
    origin: str = field(default="")
    original_url: str = field(default="")
    resource: Resource = field(default=None)

    @staticmethod
    def load(data: dict):
        from .page import Page

        if data["resource"]["type"] == "page":
            data["resource"] = Page.load(data["resource"])
        else:
            data["resource"] = Resource.load(data["resource"])

        return Link(**data)
