from abc import ABC, abstractmethod
from typing import TypedDict, Optional


class InvalidProxyConfig(Exception):
    pass


class RequestsProxyConfigDict(TypedDict):
    http: str
    https: str


class ProxyConfig(ABC):
    @abstractmethod
    def to_requests_dict(self) -> RequestsProxyConfigDict:
        pass


# TODO docs
class GenericProxyConfig(ProxyConfig):
    def __init__(self, http: Optional[str] = None, https: Optional[str] = None):
        if not http and not https:
            raise InvalidProxyConfig(
                "GenericProxyConfig requires you to define at least one of the two: "
                "http or https"
            )
        self.http = http
        self.https = https

    def to_requests_dict(self) -> RequestsProxyConfigDict:
        return {
            "http": self.http or self.https,
            "https": self.https or self.http,
        }
