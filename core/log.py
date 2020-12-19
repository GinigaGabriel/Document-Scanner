import datetime
import logging
import pathlib


def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    filename = pathlib.Path.cwd() / f'logdir/{datetime.datetime.now().strftime("%d-%m_%H-%M")}.txt'
    filename.unlink(missing_ok=True)
    filename.parent.mkdir(exist_ok=True, parents=True)
    handler = logging.FileHandler(filename)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
