from time import sleep
from numpy import linspace
import math


def make_progress_bar(n_max: float, prefix: str, gap: int,
                      length: int, with_percent = True):

    symbols = ['\u258f', '\u258e', '\u258d', '\u258c',
               '\u258b', '\u258a', '\u2589', '\u2588']

    def progress_bar(n: float) -> str:
        q = n / n_max
        print('\r' + prefix +
              ' ' * gap +
              '\u2588' * math.floor(length*q) +
              symbols[int(length*q*8)%8] +
              ' ' * math.ceil(length*(1-q)) +
              (' {:>3} %  '.format(int(100*q)) if with_percent else '  '),
              end=('' if n != n_max else '\n'), flush=True)

    return progress_bar


if __name__ == '__main__':
    n_max = 123
    num = 100
    t = 0.4
    for _ in range(100):
        progr = make_progress_bar(n_max, 'downloading..', 5, 25, True)

        for i in linspace(0, n_max, num=num):
            progr(i)
            sleep(t/num)
