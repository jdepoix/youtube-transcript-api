import sys

if sys.version_info.major == 3 and sys.version_info.minor >= 4:
    # Python 3.4+
    from html import unescape
else:
    if sys.version_info.major <= 2:
        # Python 2
        import HTMLParser

        html_parser = HTMLParser.HTMLParser()
    else:
        # Python 3.0 - 3.3
        import html.parser

        html_parser = html.parser.HTMLParser()

    def unescape(string):
        return html_parser.unescape(string)
