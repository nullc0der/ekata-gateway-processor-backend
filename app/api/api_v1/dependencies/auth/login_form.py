from typing import Optional

from fastapi.param_functions import Form


class LoginForm():
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
        two_factor_code: Optional[int] = Form(None)
    ):
        self.username = username
        self.password = password
        self.two_factor_code = two_factor_code
