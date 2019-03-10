from random import random
from time import sleep
import sys


def data():
    return random()


cnt = 0
while True:
    print(data())
    sleep(0.25)

sys.stdout.flush()
