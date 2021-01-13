import logging
import pathlib
import datetime
from core.core import *

__version__ = '1.0.0'
__author__ = 'Giniga Gabriel-Andrei'


def main():
    backend = Backend()
    
    backend.create_links()
    backend.create_output_dir()


if __name__ == "__main__":
    main()

