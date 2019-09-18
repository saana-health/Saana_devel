from logging import config
import os


LOGGING_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s.%(msecs)d [%(process)d - %(thread)d] [%(levelname)s] ' +
                       'pathname=%(pathname)s lineno=%(lineno)s ' +
                       'funcname=%(funcName)s | %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s : %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'mode': 'a',
            'formatter': 'standard',
            'filename': 'algorithm.log',
        },
        'console': {
            'level': 'CRITICAL',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'console'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}


config.dictConfig(LOGGING_SETTINGS)
DATABASE_USER = os.environ.get("DATABASE_USER", '')
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", '')

DATABASE_ADDRESS = os.environ.get('DATABASE_ADDRESS', '0.0.0.0')
DATABASE_PORT = os.environ.get('DATABASE_ADDRESS', '27017')

