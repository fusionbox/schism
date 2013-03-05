from .exceptions import SchismError
from .resources import RESOURCES


class Settings(dict):
    """
    Used for working with setting dicts for specific resource types.  If one
    attempts to access a required key that is not found, raises an exception
    with a descriptive error message.  Returns ``None`` if an optional key is
    not found.
    """
    def __init__(self, d, name, resource):
        super(Settings, self).__init__(d)

        self._name = name
        self._verbose_name = RESOURCES[resource]['verbose_name']
        self._required_settings = RESOURCES[resource]['required_settings']

    def __getitem__(self, key):
        try:
            return super(Settings, self).__getitem__(key)
        except KeyError:
            if key in self._required_settings:
                raise SchismError('Required "{key}" setting not found for "{name}" {verbose_name}'.format(
                    key=key,
                    verbose_name=self._verbose_name,
                    name=self._name,
                ))
            else:
                return None
