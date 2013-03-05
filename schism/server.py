import functools
import xmlrpclib

from .utils import log


class Server(object):
    """
    A wrapper class for connecting to and making calls to the webfaction API.
    """
    WEBFACTION_API_URL = 'https://api.webfaction.com/'

    def __init__(self, username, password):
        self._username = username
        self._password = password

        log('logging into webfaction', self._login)

    def _login(self):
        self._server = xmlrpclib.ServerProxy(self.WEBFACTION_API_URL)
        self._session_id, self._account = self._server.login(self._username, self._password)

    def __getattr__(self, name):
        """
        Attempts to find any missing attributes on the internal ServerProxy
        instance.  If found, returns a partial of the api method with the
        session_id already included as the first argument.
        """
        procedure = getattr(self._server, name)
        return functools.partial(procedure, self._session_id)
