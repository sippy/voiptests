from random import shuffle
from lib.test_config import AUTH_CREDS as AUTH_CREDS_orig

allalgs = (('SHA-512-256', 'SHA-256', 'MD5', 'MD5-sess'), \
  ('SHA-512-256', 'SHA-256', 'SHA-256-sess', 'MD5'), \
  ('SHA-512-256', 'SHA-512-256-sess', 'SHA-256', 'MD5')) \

class AUTH_CREDS(AUTH_CREDS_orig):
    enalgs = None
    realm = 'VoIPTests.NET'

    def __init__(self):
        tlist = list(allalgs)
        shuffle(tlist)
        self.enalgs = tlist[0]
        AUTH_CREDS_orig.__init__(self, 'mightyuser', 's3cr3tpAssw0Rd')
