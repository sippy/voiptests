from lib.test_config import AUTH_CREDS as AUTH_CREDS_orig
from random import shuffle

allalgs = ('SHA-256-sess', 'SHA-256', 'MD5-sess', 'MD5', None)

class AUTH_CREDS(AUTH_CREDS_orig):
    enalgs = None
    realm = 'VoIPTests.NET'

    def __init__(self):
        tlist = list(allalgs)
        shuffle(tlist)
        self.enalgs = tuple(tlist)
        AUTH_CREDS_orig.__init__(self, 'mightyuser', 's3cr3tpAssw0Rd')
