import zerorpc
from random import random
import sys


class dataRPC():
    """dataRPC"""
    def getData(self, channels="1"):
        """getData

        :param channels: channels connected to
        """
        channels = channels.split(' ')
        print("getData")
        return [random() for i in channels], [i for i in channels]

    @zerorpc.stream
    def dataStream(self, channels="1"):
        channels = channels.split(' ')
        return [random() for i in channels]


s = zerorpc.Server(dataRPC())
s.bind("tcp://0.0.0.0:4242")
s.run()
sys.stdout.flush()
