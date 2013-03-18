import functools
import os
import re
import xmlrpclib
import yaml

from .resources import RESOURCES
from .server import Server
from .settings import Settings
from .utils import log


CREATION_METHOD_RE = re.compile(r'^create_(.*)$')

valid_tasks = []


def task(fn):
    """
    Decorator adds function to an array of valid schism tasks for cli task
    argument validation.
    """
    valid_tasks.append(fn)
    return fn


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
                    verbose_name=verbose_name.capitalize(),
                    name=name,
                    ))

                if or_do:
                    log('\n')
                    return or_do(self, *args, **kwargs)
                else:
                    log('skipping...\n')
                    return

            # Otherwise, run decorated function
            else:
                return old_fn(self, *args, **kwargs)

        return new_fn

    return decorator


class Account(object):
    def __init__(self, path, run_system=False):
        self._run_system = run_system

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
        self._cache['app'] = log('Detecting existing apps', self._server.list_apps)
        self._cache['db'] = log('Detecting existing databases', self._server.list_dbs)
        self._cache['website'] = log('Detecting existing websites', self._server.list_websites)
        self._cache['domain'] = log('Detecting existing domains', self._server.list_domains)

    def _is_unique(self, resource, name):
        """
        Determines if a name for a given resource is unique.
        """
        if resource == 'domain':
            return not (name in [r['domain'] for r in self._cache[resource]])
        else:
            return not (name in [r['name'] for r in self._cache[resource]])

    @task
    def provision(self):
        # Upload files
        if self._config.get('files'):
            for local_path, remote_path in self._config['files'].iteritems():
                self.write_file(remote_path, local_path)

        # Create domains
        if not self._config.get('domains'):
            log('No domains specified...skipping\n')
        else:
            for domain in self._config['domains']:
                self.create_domain(domain)

        # Create databases
        if not self._config.get('databases'):
            log('No databases specified...skipping\n')
        else:
            for db_name, db_settings in self._config['databases'].iteritems():
                settings = Settings(db_settings, name=db_name, resource='db')

                db_type = settings['type']
                db_password = settings['password']

                self.create_db(db_name, db_type, db_password)

        # Create applications
        if not self._config.get('applications'):
            log('No applications specified...skipping\n')
        else:
            for app_name, app_settings in self._config['applications'].iteritems():
                settings = Settings(app_settings, name=app_name, resource='app')

                app_type = settings['type']

                self.create_app(app_name, app_type)

        # Create websites
        if not self._config.get('websites'):
            log('No websites specified...skipping\n')
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

        # Configure crontab
        cronjobs = self._config.get('cronjobs')
        if cronjobs:
            cronjobs_present = cronjobs.get('present', [])
            cronjobs_purged = cronjobs.get('purged', [])

            for line in cronjobs_present:
                self.create_cronjob(line)
            for line in cronjobs_purged:
                self.delete_cronjob(line)

        # Execute system commands
        if self._run_system and self._config.get('system'):
            for cmd in self._config['system']:
                self.system(cmd)

    def write_file(self, remote_path, local_path, mode='wb'):
        with open(os.path.join('files', local_path), 'rb') as f:
            content = f.read()

        # Some juggling to warn about overwriting files
        try:
            self._server.system('ls ~/{0}'.format(remote_path))
        except xmlrpclib.Fault as e:
            # Pass any other errors through
            if 'No such file' not in e.faultString:
                raise

            # Otherwise, no such file.  Create parent directories and continue.
            dir_path = remote_path.rsplit('/', 1)
            if len(dir_path) == 2:
                self._server.system('mkdir -p ~/{0}'.format(dir_path[0]))
        else:
            if raw_input('Remote file ~/{0} already exists. Overwrite? (Y/n) '.format(remote_path)) != 'Y':
                log('skipping...\n')
                return

        log(
            'Copying local:{local_path} -> webfaction:~/{remote_path} '.format(
                local_path=local_path,
                remote_path=remote_path,
            ),
            self._server.write_file,
            remote_path,
            content,
            mode,
        )

    @require_unique()
    def create_domain(self, domain):
        log(
            'Creating "{domain}" domain'.format(domain=domain),
            self._server.create_domain,
            domain,
        )

    @require_unique()
    def create_db(self, name, type, password):
        log(
            'Creating "{name}" database with type "{type}"'.format(name=name, type=type),
            self._server.create_db,
            name,
            type,
            password,
        )

    @require_unique()
    def create_app(self, name, type, autostart=False):
        log(
            'Creating "{name}" application with type "{type}"'.format(name=name, type=type),
            self._server.create_app,
            name,
            type,
        )

    def update_website(self, name, ip, https, subdomains, site_apps=None):
        args = [
            'Updating "{name}" website'.format(name=name),
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
            'Creating "{name}" website'.format(name=name),
            self._server.create_website,
            name,
            ip,
            https,
            subdomains,
        ]
        if site_apps:
            args += site_apps

        log(*args)

    def create_cronjob(self, line):
        log('Ensuring present in crontab:\n{line}\n'.format(line=line))
        self._server.delete_cronjob(line)
        self._server.create_cronjob(line)

    def delete_cronjob(self, line):
        log('Purging from crontab:\n{line}\n'.format(line=line))
        self._server.delete_cronjob(line)

    def system(self, cmd):
        normalized = 'cd ~/ && {0}'.format(cmd)

        log('Executing: {cmd}\n'.format(cmd=cmd))
        out = self._server.system(normalized)
        if out.strip():
            log('Out: {out}\n'.format(out=out))
