"""
Module with the logging related configurations and methods
"""
import datetime
import logging.config
import pathlib

path = pathlib.Path.cwd() / f"logdir/{datetime.datetime.now().strftime('%d-%m_%H-%M-%S')}.txt"

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'ds.formatter': {
            'format': '%(levelname)-8s %(asctime)s %(name)s -> %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '%'
        }
    },

    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': f'{path}',
            'mode': 'a',
            'formatter': 'ds.formatter'
        }
    }

}


def configure_logger():
    print(path)
    logging.config.dictConfig(LOGGING_CONFIG)
