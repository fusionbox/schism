"""
Describes all resource types available through the webfaction API.
"""
RESOURCES = {
    'app': {
        'verbose_name': 'application',
        'verbose_name_plural': 'applications',
        'required_settings': ('type',),
    },
    'db': {
        'verbose_name': 'database',
        'verbose_name_plural': 'databases',
        'required_settings': ('type', 'password'),
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
