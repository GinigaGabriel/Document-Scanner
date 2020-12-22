from core.root import root
from core.log import setup_custom_logger

__version__ = '1.0.0'
__author__ = 'Giniga Gabriel Andrei'

LOGGER = setup_custom_logger('root')
LOGGER.info(f"Document Scanner v{__version__}")
LOGGER.info(f"Created by {__author__}")

if __name__ == "__main__":
    LOGGER.info('Executing root()')
    root()
