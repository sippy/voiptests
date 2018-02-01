from random import random

def genIP(atype = None):
    if (atype == None and random() > 0.5) or atype == 'IP4':
        a = 1 + int(255.0 * random())
        b = int(256.0 * random())
        c = int(256.0 * random())
        d = 1 + int(255.0 * random())
        return ('IP4', '%d.%d.%d.%d' % (a, b, c, d))
    raddr = '2001'
    for x in range(0, 7):
        b = random()
        if b > 0.5:
            a = 0
        else:
            a = int(random() * 65536.0)
        raddr += ':%x' % a
    return ('IP6', raddr)

if __name__ == '__main__':
    while True:
        print(genIP())
