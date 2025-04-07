from pydantic import constr

from schemas.base import EmptySchema, BaseSchema


class UserNameSchema(EmptySchema):
    username: constr(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-ßöäüÖÄÜ]+$")


class UserPasswordChangeSchema(EmptySchema):
    old_password: constr(min_length=5, max_length=50)
    new_password: constr(min_length=5, max_length=50)


class UserCreateSchema(UserNameSchema):
    password: constr(min_length=5, max_length=50)


class UserSchema(UserNameSchema, BaseSchema):
    pass


class UserLoginSchema(EmptySchema):
    jwt_token: str
    username: str
    id: str
