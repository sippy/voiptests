class TestException(Exception):
    pass

class SDPValidationFailure(TestException):
    pass

class ScenarioFailure(TestException):
    pass
