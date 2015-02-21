from random import random

def genIP():
    a = 1 + int(255.0 * random())
    b = int(256.0 * random())
    c = int(256.0 * random())
    d = 1 + int(255.0 * random())
    return '%d.%d.%d.%d' % (a, b, c, d)

if __name__ == '__main__':
    while True:
        print genIP()
