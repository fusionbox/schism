import functools
import re
import yaml

from .resources import RESOURCES
from .server import Server
from .settings import Settings
from .utils import log


CREATION_METHOD_RE = re.compile(r'^create_(.*)$')


def require_unique(or_do=None):
    """
    Returns a decorator that decorates a resource creation method to require
    that the name of the resource being created is unique.  An alternative
    method may be specified using ``or_do`` which will be called if the name is
    not unique.
    """
    def decorator(old_fn):
        @functools.wraps(old_fn)
        def new_fn(self, *args, **kwargs):
            # Detect resource type
            resource = CREATION_METHOD_RE.search(old_fn.func_name).group(1)
            verbose_name = RESOURCES[resource]['verbose_name']

            name = args[0]

            # If resource name not unique, abort
            if not self._is_unique(resource, name):
                log('{verbose_name} with name "{name}" already exists...'.format(
                    verbose_name=verbose_name,
                    name=name,
                    ))

                if or_do:
                    return or_do(self, *args, **kwargs)
                else:
                    log('skipping <!>\n')
                    return

            # Otherwise, run decorated function
            else:
                return old_fn(self, *args, **kwargs)

        return new_fn

    return decorator


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
        if resource == 'domain':
            return not (name in [r['domain'] for r in self._cache[resource]])
        else:
            return not (name in [r['name'] for r in self._cache[resource]])

    def provision(self):
        # Create domains
        if not self._config.get('domains'):
            log('no domains specified...skipping <!>\n')
        else:
            for domain in self._config['domains']:
                self.create_domain(domain)

        # Create applications
        if not self._config.get('applications'):
            log('no applications specified...skipping <!>\n')
        else:
            for app_name, app_settings in self._config['applications'].iteritems():
                settings = Settings(app_settings, name=app_name, resource='app')

                app_type = settings['type']

                self.create_app(app_name, app_type)

        # Create databases
        if not self._config.get('databases'):
            log('no databases specified...skipping <!>\n')
        else:
            for db_name, db_settings in self._config['databases'].iteritems():
                settings = Settings(db_settings, name=db_name, resource='db')

                db_type = settings['type']
                db_password = settings['password']

                self.create_db(db_name, db_type, db_password)

        # Create websites
        if not self._config.get('websites'):
            log('no websites specified...skipping <!>\n')
        else:
            for website_name, website_settings in self._config['websites'].iteritems():
                settings = Settings(website_settings, name=website_name, resource='website')

                website_ip = settings['ip']
                website_https = settings['https']
                website_subdomains = settings['subdomains']
                website_site_apps = settings['site_apps']

                self.create_website(
                    website_name,
                    website_ip,
                    website_https,
                    website_subdomains,
                    website_site_apps,
                )

    @require_unique()
    def create_domain(self, domain):
        log(
            'creating "{domain}" domain'.format(domain=domain),
            self._server.create_domain,
            domain,
        )

    @require_unique()
    def create_app(self, name, type, autostart=False):
        log(
            'creating "{name}" application with type "{type}"'.format(name=name, type=type),
            self._server.create_app,
            name,
            type,
        )

    @require_unique()
    def create_db(self, name, type, password):
        log(
            'creating "{name}" database with type "{type}"'.format(name=name, type=type),
            self._server.create_db,
            name,
            type,
            password,
        )

    def update_website(self, name, ip, https, subdomains, site_apps=None):
        args = [
            'updating "{name}" website'.format(name=name),
            self._server.update_website,
            name,
            ip,
            https,
            subdomains,
        ]
        if site_apps:
            args += site_apps

        log(*args)

    @require_unique(or_do=update_website)
    def create_website(self, name, ip, https, subdomains, site_apps=None):
        args = [
            'creating "{name}" website'.format(name=name),
            self._server.create_website,
            name,
            ip,
            https,
            subdomains,
        ]
        if site_apps:
            args += site_apps

        log(*args)
