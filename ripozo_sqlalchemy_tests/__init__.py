from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo_sqlalchemy_tests import unit, integration

from logging import config

try:
    config.dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s| %(name)s/%(process)d: %(message)s @%(funcName)s:%(lineno)d #%(levelname)s'
                }
            },
            'handlers': {
                'console': {
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler'
                }
            },
            'root': {
                'handlers': ['console'],
                'level': "WARNING"
            },
            'ripozo_sqlalchemy': {
                'handlers': ['console'],
                'level': 'DEBUG'
            }
        }
    )
except AttributeError:
    pass
