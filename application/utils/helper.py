# coding: utf-8
import signal


def parse_int(integer, default=None):
    """提取整数，若失败则返回default值"""
    try:
        return int(integer)
    except Exception, e:
        return default


class Timeout():
    """Timeout class using ALARM signal."""

    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)  # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()