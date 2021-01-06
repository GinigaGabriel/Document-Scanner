import logging
import pathlib
import datetime
from core.needed import Backend
from core.log import configure_logger

__version__ = '1.0.0'
__author__ = 'Giniga Gabriel-Andrei'

configure_logger()

logger = logging.getLogger(__name__)

logger.info(f"Document Scanner v{__version__}")
logger.info(f"Created by {__author__}")


def main():
    resource = Backend()
    logger.info('daaa111111')
    for index, (name, command) in enumerate(resource.commands, 1):
        logger.info(f'DS -> Executing `{name}` [{index}/{len(resource.commands)}]')
        status = command()
        if status:
            logger.error(f'ERROR: Document Scanner execution failed at {name}')
            exit(1)


if __name__ == "__main__":
    logger.info('Executing root()')
    main()
