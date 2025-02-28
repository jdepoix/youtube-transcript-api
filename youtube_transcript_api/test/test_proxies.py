import pytest

from youtube_transcript_api.proxies import GenericProxyConfig, InvalidProxyConfig


class TestGenericProxyConfig:
    def test_to_requests_dict(self):
        proxy_config = GenericProxyConfig(
            http="http://myproxy.com",
            https="https://myproxy.com",
        )

        print(proxy_config.to_requests_dict)
        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "http://myproxy.com",
            "https": "https://myproxy.com",
        }

    def test_to_requests_dict__only_http(self):
        proxy_config = GenericProxyConfig(
            http="http://myproxy.com",
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "http://myproxy.com",
            "https": "http://myproxy.com",
        }

    def test_to_requests_dict__only_https(self):
        proxy_config = GenericProxyConfig(
            https="https://myproxy.com",
        )

        request_dict = proxy_config.to_requests_dict()

        assert request_dict == {
            "http": "https://myproxy.com",
            "https": "https://myproxy.com",
        }

    def test__invalid_config(self):
        with pytest.raises(InvalidProxyConfig):
            GenericProxyConfig()
