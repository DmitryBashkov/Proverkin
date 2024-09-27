class NewUserException(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return f'Cannot create new user: {self.response}'