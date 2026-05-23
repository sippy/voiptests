class spinor(object):
    i = 0
    busy_states = '-\\|/'
    idle_states = '.oOo'
    idle = False

    def tick(self):
        if self.idle:
            st = self.idle_states
        else:
            st = self.busy_states
        ri = self.i % len(st)
        rv = st[ri]
        self.i += 1
        return rv
