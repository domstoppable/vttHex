import os
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

from server import application

if __name__ == '__main__':
    application.run()
