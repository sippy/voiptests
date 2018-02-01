from random import random

class PortRange(object):
    abs_minp = 1024
    abs_maxp = 65535
    minp = None
    maxp = None

    def __init__(self, s):
        sparts = s.split('-', 1)
        self.minp, self.maxp = int(sparts[0]), int(sparts[1])
        if self.minp < self.abs_minp or self.maxp > self.abs_maxp:
            raise ValueError('Invalid portrange: %s' % s)

    def gennotinrange(self):
        while True:
            portn = 2 * (1 + int(32765.0 * random()))
            if (portn >= self.abs_minp and portn <= self.abs_maxp) and \
              (portn < self.minp or portn > self.maxp):
                return portn

    def isinrange(self, portn):
        if portn < self.minp or portn > self.maxp:
            return False
        return True

if __name__ == '__main__':
    pr = PortRange('16-65500')
    for i in range(0, 10):
        print(pr.gennotinrange())
    print(pr.isinrange(4))
    print(pr.isinrange(36))
    print(pr.isinrange(21311))
    print(pr.isinrange(65502))
