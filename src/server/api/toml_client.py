from requests import request
import toml


class TomlClient(object):
    """
    This class provides a dict-like interface to a remote TOML resource hosted
    on the web.
    """

    def __init__(self, request=request, base_url=None, headers=None):
        self.request = request
        self.base_url = base_url
        self.headers = headers
        self.last_exception = None

    def __getitem__(self, key):
        try:
            print("self.request({}, {}, headers={})".format(
                'GET',
                self.base_url,
                self.headers,
            ))
            r = self.request(
                'GET',
                self.base_url,
                headers=self.headers,
            )
            r.raise_for_status()
            text = r.text
            print("  == {}".format(text))
            value = toml.loads(text)[key]
            r.close()
            return value
        except Exception as e:
            self.last_exception = e
            raise KeyError(key)
