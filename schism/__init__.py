import functools
import re
import sys
import xmlrpclib
import yaml


RESOURCES = {
    'app': {
        'verbose_name': 'application',
        'verbose_name_plural': 'applications',
    },
    'db': {
        'verbose_name': 'database',
        'verbose_name_plural': 'databases',
    },
    'website': {
        'verbose_name': 'website',
        'verbose_name_plural': 'websites',
    },
    'domain': {
        'verbose_name': 'domain',
        'verbose_name_plural': 'domains',
    },
}


def log(message, func=None, *args, **kwargs):
    """
    Logs a message to stderr.  If a function and arguments are specified, runs
    the function with the given arguments and logs additional messages to
    indicate status.
    """
    sys.stderr.write('{0}'.format(message.capitalize()))

    if func:
        sys.stderr.write('...')
        value = func(*args, **kwargs)
        sys.stderr.write('done\n')
        return value


require_unique_re = re.compile(r'^create_(.*)$')


def require_unique(old_fn):
    @functools.wraps(old_fn)
    def new_fn(self, *args, **kwargs):
        # Detect resource type
        resource = require_unique_re.search(old_fn.func_name).group(1)
        verbose_name = RESOURCES[resource]['verbose_name']

        name = args[0]

        # If resource name not unique, abort
        if not self._is_unique(resource, name):
            log('{verbose_name} with name "{name}" already exists...skipping <!>\n'.format(
                verbose_name=verbose_name,
                name=name,
                ))
            return
        # Otherwise, run decorated function
        else:
            old_fn(self, *args, **kwargs)

    return new_fn


class SchismError(Exception):
    pass


class Server(object):
    """
    A wrapper class for connecting and making calls to the webfaction API.
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
        procedure = getattr(self._server, name)
        return functools.partial(procedure, self._session_id)


class Options(dict):
    """
    Used for working with resource setting dicts.  Allows the specification of
    required settings (dictionary keys).  If one attempts to access a required
    key that is not found, raises an exception with a descriptive error
    message.  Returns ``None`` if a non-required key is not found.
    """
    def __init__(self, d, resource_name, resource_type, required=None):
        super(Options, self).__init__(d)

        self._resource_name = resource_name
        self._resource_type = resource_type
        self._required = required

    def __getitem__(self, key):
        try:
            return super(Options, self).__getitem__(key)
        except KeyError:
            if key in self._required:
                raise SchismError('Required "{key}" setting not specified for "{resource_name}" {resource_type}'.format(
                    key=key,
                    resource_type=self._resource_type,
                    resource_name=self._resource_name,
                ))
            else:
                return None


class Account(object):
    def __init__(self, path):
        # Open and load yaml config
        with open(path, 'r') as f:
            c = yaml.load(f.read())
            self._config = c

        # Connect
        self._server = Server(**self._config['account'])

        # Detect existing resources
        self._build_cache()

    def _build_cache(self):
        """
        Builds a cache of existing resource information for the webfaction
        account.
        """
        self._cache = {}
        self._cache['app'] = log('detecting existing apps', self._server.list_apps)
        self._cache['db'] = log('detecting existing databases', self._server.list_dbs)
        self._cache['website'] = log('detecting existing websites', self._server.list_websites)
        self._cache['domain'] = log('detecting existing domains', self._server.list_domains)

    def _is_unique(self, resource, name):
        """
        Determines if a name for a given resource is unique.
        """
        return not (name in [r['name'] for r in self._cache[resource]])

    def provision(self):
        # Create applications
        if not self._config.get('applications'):
            log('no applications specified...skipping <!>\n')

        for app_name, app_options in self._config['applications'].iteritems():
            options = Options(
                app_options,
                resource_name=app_name,
                resource_type='application',
                required=('type',),
            )

            app_type = options['type']
            self.create_app(app_name, app_type)

        # Create databases
        if not self._config.get('databases'):
            log('no databases specified...skipping <!>\n')

        for db_name, db_options in self._config['databases'].iteritems():
            options = Options(
                db_options,
                resource_name=db_name,
                resource_type='database',
                required=('type',),
            )

            db_type = options['type']
            self.create_db(db_name, db_type)

    @require_unique
    def create_app(self, name, type, autostart=False):
        log(
            'creating "{name}" application with type "{type}"'.format(name=name, type=type),
            self._server.create_app,
            name,
            type,
        )

    @require_unique
    def create_db(self, name, type, password):
        log(
            'creating "{name}" database with type "{type}"'.format(name=name, type=type),
            self._server.create_db,
            name,
            type,
            password,
        )
