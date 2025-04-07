from sqlalchemy import Column, Integer, LargeBinary, String, Boolean
import bcrypt

from models.base import BaseModel


class UserModel(BaseModel):
    __tablename__ = "user"

    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    guest = Column(Boolean, nullable=False, default=False)
    profile_picture_data = Column(LargeBinary, nullable=True)
    profile_picture_type = Column(String, nullable=True)
    profile_picture_name = Column(String, nullable=True)

    def set_password(self, password):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        self.password = hashed_password.decode()

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password.encode())
