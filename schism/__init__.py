import xmlrpclib
import yaml
import functools
import sys


def run_with_message(message, func, *args, **kwargs):
    sys.stderr.write(message + '...')
    value = func(*args, **kwargs)
    sys.stderr.write('done\n')
    return value


class SchismError(Exception):
    pass


class Server(object):
    WEBFACTION_API_ENDPOINT = 'https://api.webfaction.com/'

    def __init__(self, username, password):
        self._username = username
        self._password = password

        sys.stderr.write('Logging into webfaction...')
        self._server = xmlrpclib.ServerProxy(self.WEBFACTION_API_ENDPOINT)
        self._session_id, self._account = self._server.login(self._username, self._password)
        sys.stderr.write('done\n')

    def __getattr__(self, name):
        procedure = getattr(self._server, name)
        return functools.partial(procedure, self._session_id)


class Session(object):
    def __init__(self, path):
        with open(path, 'r') as f:
            self._config = yaml.load(f.read())

        s = Server(**self._config['account'])
        self._server = s

        self._apps = run_with_message('Detecting existing apps', s.list_apps)
        self._websites = run_with_message('Detecting existing websites', s.list_websites)
        self._domains = run_with_message('Detecting existing domains', s.list_domains)

        self.provision()

    def provision(self):
        for app_name, app_options in self._config['applications']:
            # Require type
            try:
                app_type = app_options['type']
            except KeyError:
                raise SchismError('No application type specified for "{0}" application'.format(
                    app_name,
                ))
            self.create_app(app_name, app_type)
        else:
            raise SchismError('No applications specified')

    def create_app(self, name, type, autostart=False):
        # Require unique app name, create
        if name in [app.name for app in self._apps]:
            sys.stderr.write('An application with the name "{0}" already exists...skipping\n'.format(
                name,
            ))
            return
        else:
            #run_with_message(
                #'Creating "{name}" application with type "{type}"'.format(
                    #name=name,
                    #type=type,
                #),
                #self._server.create_app,
                #name,
                #type,
            #)
