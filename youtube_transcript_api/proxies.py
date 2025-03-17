from abc import ABC, abstractmethod
from typing import TypedDict, Optional


class InvalidProxyConfig(Exception):
    pass


class RequestsProxyConfigDict(TypedDict):
    """
    This type represents the Dict that is used by the requests library to configure
    the proxies used. More information on this can be found in the official requests
    documentation: https://requests.readthedocs.io/en/latest/user/advanced/#proxies
    """

    http: str
    https: str


class ProxyConfig(ABC):
    """
    The base class for all proxy configs. Anything can be a proxy config, as longs as
    it can be turned into a `RequestsProxyConfigDict` by calling `to_requests_dict`.
    """

    @abstractmethod
    def to_requests_dict(self) -> RequestsProxyConfigDict:
        """
        Turns this proxy config into the Dict that is expected by the requests library.
        More information on this can be found in the official requests documentation:
        https://requests.readthedocs.io/en/latest/user/advanced/#proxies
        """
        pass

    @property
    def prevent_keeping_connections_alive(self) -> bool:
        """
        If you are using rotating proxies, it can be useful to prevent the HTTP
        client from keeping TCP connections alive, as your IP won't be rotated on
        every request, if your connection stays open.
        """
        return False

    @property
    def retries_when_blocked(self) -> int:
        """
        Defines how many times we should retry if a request is blocked. When using
        rotating residential proxies with a large IP pool it can make sense to retry a
        couple of times when a blocked IP is encountered, since a retry will trigger
        an IP rotation and the next IP might not be blocked.
        """
        return 0


class GenericProxyConfig(ProxyConfig):
    """
    This proxy config can be used to set up any generic HTTP/HTTPS/SOCKS proxy. As it
    the requests library is used under the hood, you can follow the requests
    documentation to get more detailed information on how to set up proxies:
    https://requests.readthedocs.io/en/latest/user/advanced/#proxies

    If only an HTTP or an HTTPS proxy is provided, it will be used for both types of
    connections. However, you will have to provide at least one of the two.
    """

    def __init__(self, http_url: Optional[str] = None, https_url: Optional[str] = None):
        """
        If only an HTTP or an HTTPS proxy is provided, it will be used for both types of
        connections. However, you will have to provide at least one of the two.

        :param http_url: the proxy URL used for HTTP requests. Defaults to `https_url`
            if None.
        :param https_url: the proxy URL used for HTTPS requests. Defaults to `http_url`
            if None.
        """
        if not http_url and not https_url:
            raise InvalidProxyConfig(
                "GenericProxyConfig requires you to define at least one of the two: "
                "http or https"
            )
        self.http_url = http_url
        self.https_url = https_url

    def to_requests_dict(self) -> RequestsProxyConfigDict:
        return {
            "http": self.http_url or self.https_url,
            "https": self.https_url or self.http_url,
        }


class WebshareProxyConfig(GenericProxyConfig):
    """
    Webshare is a provider offering rotating residential proxies, which is the
    most reliable way to work around being blocked by YouTube.

    If you don't have a Webshare account yet, you will have to create one
    at https://www.webshare.io/?referral_code=w0xno53eb50g and purchase a "Residential"
    proxy package that suits your workload, to be able to use this proxy config (make
    sure NOT to purchase "Proxy Server" or "Static Residential"!).

    Once you have created an account you only need the "Proxy Username" and
    "Proxy Password" that you can find in your Webshare settings
    at https://dashboard.webshare.io/proxy/settings to set up this config class, which
    will take care of setting up your proxies as needed, by defaulting to rotating
    proxies.

    Note that referral links are used here and any purchases made through these links
    will support this Open Source project, which is very much appreciated! :)
    However, you can of course integrate your own proxy solution by using the
    `GenericProxyConfig` class, if that's what you prefer.
    """

    DEFAULT_DOMAIN_NAME = "p.webshare.io"
    DEFAULT_PORT = 80

    def __init__(
        self,
        proxy_username: str,
        proxy_password: str,
        retries_when_blocked: int = 10,
        domain_name: str = DEFAULT_DOMAIN_NAME,
        proxy_port: int = DEFAULT_PORT,
    ):
        """
        Once you have created a Webshare account at
        https://www.webshare.io/?referral_code=w0xno53eb50g and purchased a
        "Residential" package (make sure NOT to purchase "Proxy Server" or
        "Static Residential"!), this config class allows you to easily use it,
        by defaulting to the most reliable proxy settings (rotating residential
        proxies).

        :param proxy_username: "Proxy Username" found at
            https://dashboard.webshare.io/proxy/settings
        :param proxy_password: "Proxy Password" found at
            https://dashboard.webshare.io/proxy/settings
        :param retries_when_blocked: Define how many times we should retry if a request
            is blocked. When using rotating residential proxies with a large IP pool it
            makes sense to retry a couple of times when a blocked IP is encountered,
            since a retry will trigger an IP rotation and the next IP might not be
            blocked. Defaults to 10.
        """
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.domain_name = domain_name
        self.proxy_port = proxy_port
        self._retries_when_blocked = retries_when_blocked

    @property
    def url(self) -> str:
        return (
            f"http://{self.proxy_username}-rotate:{self.proxy_password}"
            f"@{self.domain_name}:{self.proxy_port}/"
        )

    @property
    def http_url(self) -> str:
        return self.url

    @property
    def https_url(self) -> str:
        return self.url

    @property
    def prevent_keeping_connections_alive(self) -> bool:
        return True

    @property
    def retries_when_blocked(self) -> int:
        return self._retries_when_blocked
