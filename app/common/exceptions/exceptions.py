'''Class For Customised Exceptions'''
# pylint:disable = redefined-builtin,missing-function-docstring
class Unauthorized(Exception):
    '''Handles 401 Unauthorized Errors'''

    def __init__(self, message, data=None):
        super().__init__()
        self.status_code = 401
        self.message = message
        self.status = "401 Unauthorized"
        self.data = data

    def to_dict(self):
        rv = dict(self.data or ())
        rv['status'] = self.status
        rv['message'] = self.message
        rv['data'] = self.data
        return rv


class InternalError(Exception):
    '''Handles 500 Internal Error exception'''

    def __init__(self, message, data=None):
        super().__init__()
        self.status_code = 500
        self.message = message
        self.status = "500 Internal Server Error"
        self.data = data

    def to_dict(self):
        rv = dict(self.data or ())
        rv['status'] = self.status
        rv['message'] = self.message
        rv['data'] = self.data
        return rv


class NotFound(Exception):
    '''Handles 404 Not Found Errors'''
    def __init__(self, message, data=None):
        super().__init__()
        self.status_code = 404
        self.message = message
        self.status = "404 Not Found"
        self.data = data

    def to_dict(self):
        rv = dict(self.data or ())
        rv['status'] = self.status
        rv['message'] = self.message
        rv['data'] = self.data
        return rv


class UnprocessableEntity(Exception):
    '''Handles 422 Unprocessable error'''
    def __init__(self, message, data=None):
        super().__init__()
        self.status_code = 422
        self.message = message
        self.status = "422 Unprocessable Entity"
        self.data = data

    def to_dict(self):
        rv = dict(self.data or ())
        rv['status'] = self.status
        rv['message'] = self.message
        rv['data'] = self.data
        return rv

