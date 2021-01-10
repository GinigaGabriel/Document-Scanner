import logging
import pathlib
import datetime

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    handler = logging.FileHandler(filename=pathlib.Path.cwd() / f'logdir/{datetime.datetime.now().strftime("%d-%m_%H-%M-%S")}.txt')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger