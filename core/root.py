import pathlib

import logging
import os
from core.needed import *
from ui.gui import *

logger = logging.getLogger('root')


def root():
    resource = Backend()
    resource.create_signals()


    # for index, (name, command) in enumerate(resource.commands, 1):
    #     logger.info(f'DS -> Executing `{name}` [{index}/{len(resource.commands)}]')
    #     status = command()
    #     if status:
    #         logger.error(f'ERROR: Document Scanner execution failed at {name}')
    #         sys.exit(app.exec_()) exit(1)
