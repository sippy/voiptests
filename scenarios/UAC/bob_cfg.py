from lib.test_config import AUTH_CREDS as AUTH_CREDS_orig

class AUTH_CREDS(AUTH_CREDS_orig):
    enalgs = ('SHA-512-256', 'SHA-256', 'MD5', 'MD5-sess')
    realm = 'VoIPTests.NET'

    def __init__(self):
        AUTH_CREDS_orig.__init__(self, 'mightyuser', 's3cr3tpAssw0Rd')
