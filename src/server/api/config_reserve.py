class ConfigReserve(object):
    """
    This class provides a reconfigurable union of configuration sources,
    which looks more or less like a Python dictionary, but provides the
    ability to reload configuration data dynamically.

    Once a key is acquired, it is memoized for future use, making it very
    cheap to access in the normal case.  The only time a configuration setting
    may incur any overhead is when the local memo cache is invalidated.
    """

    def __init__(self):
        self.sources = []
        self.reconfigure()

    def with_config_source(self, src):
        """
        Appends the given configuration source to the list of configuration
        sources.
        """
        self.sources.append(src)
        return self

    def __getitem__(self, key):
        if key in self.memo_cache:
            print("Found {} in cache: {}".format(key, self.memo_cache[key]))
            return self.memo_cache[key]

        for source in self.sources:
            try:
                value = source[key]
                self.memo_cache[key] = value
                print("Memoized {} in cache: {}".format(key, self.memo_cache[key]))
                return value
            except KeyError as e:
                if e[0] == key:
                    continue
                else:
                    raise
        # We've reached the end of the sources list, OR, no source has any
        # idea what you're looking for.  Raise a KeyError just like a dict
        # would.
        raise KeyError(key)

    def reconfigure(self):
        """
        Blows out the memoized configurations, so that they are refreshed from
        their respective configuration sources once more.  In effect, this
        allows new configurations to take effect.
        """
        self.memo_cache = {}
