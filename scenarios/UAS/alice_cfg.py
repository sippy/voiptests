from lib.test_config import AUTH_CREDS as AUTH_CREDS_orig

allargs = [(None, 'MD5',), ('MD5-sess',), ('SHA-256',),  ('SHA-256-sess',),
  ('SHA-256', 'SHA-256-sess', 'MD5-sess', None)]

class AUTH_CREDS(AUTH_CREDS_orig):
    def __init__(self):
        self.enalgs = allargs.pop()
        allargs.insert(0, self.enalgs)
        AUTH_CREDS_orig.__init__(self, 'mightyuser', 's3cr3tpAssw0Rd')
