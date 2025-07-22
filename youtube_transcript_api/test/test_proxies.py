import pytest

from youtube_transcript_api.proxies import (
    GenericProxyConfig,
    InvalidProxyConfig,
    WebshareProxyConfig,
)


class TestGenericProxyConfig:
    def test_to_requests_dict(self):
        proxy_config = GenericProxyConfig(
            http_url="http://myproxy.com",
            https_url="https://myproxy.com",
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "http://myproxy.com",
            "https": "https://myproxy.com",
        }

    def test_to_requests_dict__only_http(self):
        proxy_config = GenericProxyConfig(
            http_url="http://myproxy.com",
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "http://myproxy.com",
            "https": "http://myproxy.com",
        }

    def test_to_requests_dict__only_https(self):
        proxy_config = GenericProxyConfig(
            https_url="https://myproxy.com",
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "https://myproxy.com",
            "https": "https://myproxy.com",
        }

    def test__invalid_config(self):
        with pytest.raises(InvalidProxyConfig):
            GenericProxyConfig()


class TestWebshareProxyConfig:
    def test_to_requests_dict(self):
        proxy_config = WebshareProxyConfig(
            proxy_username="user",
            proxy_password="password",
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "http://user-rotate:password@p.webshare.io:80/",
            "https": "http://user-rotate:password@p.webshare.io:80/",
        }

    def test_to_requests_dict__with_location_filter(self):
        proxy_config = WebshareProxyConfig(
            proxy_username="user",
            proxy_password="password",
            filter_ip_locations=["us"],
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "http://user-US-rotate:password@p.webshare.io:80/",
            "https": "http://user-US-rotate:password@p.webshare.io:80/",
        }

    def test_to_requests_dict__with_multiple_location_filters(self):
        proxy_config = WebshareProxyConfig(
            proxy_username="user",
            proxy_password="password",
            filter_ip_locations=["de", "us"],
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "http://user-DE-US-rotate:password@p.webshare.io:80/",
            "https": "http://user-DE-US-rotate:password@p.webshare.io:80/",
        }
