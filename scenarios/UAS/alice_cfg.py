from lib.test_config import AUTH_CREDS as AUTH_CREDS_orig

class AUTH_CREDS(AUTH_CREDS_orig):
    enalgs = ('MD5', None)

    def __init__(self):
        AUTH_CREDS_orig.__init__(self, 'mightyuser', 's3cr3tpAssw0Rd')
