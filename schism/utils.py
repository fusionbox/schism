import sys


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
