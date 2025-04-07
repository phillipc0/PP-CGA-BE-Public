import io
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import StreamingResponse

from dependencies import get_db, verify_jwt
from models.user import UserModel
from schemas.user import UserCreateSchema, UserLoginSchema, UserPasswordChangeSchema, UserSchema
from util.generic import gen_token, generate_random_string
from util.guestname import generate_random_name_and_check_if_exists

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(user_id: str, db: Session = Depends(get_db), user: UserModel = Depends(verify_jwt)):
    return db.query(UserModel).filter_by(id=user_id).one()


@router.get("", response_model=list[UserSchema])
async def user_list(db: Session = Depends(get_db), user: UserModel = Depends(verify_jwt)):
    return db.query(UserModel).all()


@router.post("/register", response_model=UserLoginSchema)
async def user_create(user: UserCreateSchema, db: Session = Depends(get_db)):
    new_user = UserModel(
        username=user.username
    )
    new_user.set_password(user.password)
    db.add(new_user)
    db.commit()
    token = gen_token(new_user)
    return {"jwt_token": token.encode("UTF-8"), "username": new_user.username, "id": new_user.id}


@router.put("/password", response_model=UserSchema)
async def user_changepassword(password_data: UserPasswordChangeSchema, db: Session = Depends(get_db),
                              user: UserModel = Depends(verify_jwt)):
    if not user.verify_password(password_data.old_password):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid current password"
        )
    user.set_password(password_data.new_password)
    db.commit()
    return user


@router.post("/login", response_model=UserLoginSchema)
async def user_login(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter_by(username=user_data.username).one()
    if not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid password"
        )
    token = gen_token(user)
    return {"jwt_token": token.encode("UTF-8"), "username": user.username, "id": user.id}


@router.post("/guest", response_model=UserLoginSchema)
async def guest_login(db: Session = Depends(get_db)):
    new_user = UserModel(
        guest=True,
        username=generate_random_name_and_check_if_exists(db)
    )
    new_user.set_password(generate_random_string(15))

    db.add(new_user)
    db.commit()
    token = gen_token(new_user)
    return {"jwt_token": token.encode("UTF-8"), "username": new_user.username, "id": new_user.id}


# noinspection PyTypeChecker
@router.get("/{user_id}/profile_picture", response_class=StreamingResponse)
async def get_profile_picture(user_id: str, db: Session = Depends(get_db), user: UserModel = Depends(verify_jwt)):
    user = db.query(UserModel).filter_by(id=user_id).one()
    if not user.profile_picture_data:
        raise HTTPException(status_code=404, detail="Profile picture not found")
    file_like = io.BytesIO(user.profile_picture_data)
    return StreamingResponse(file_like, media_type=user.profile_picture_type,
                             headers={"Content-Disposition": f"attachment; filename={user.profile_picture_name}"})


@router.put("/profile_picture", response_model=UserSchema)
async def set_profile_picture(profile_picture: UploadFile = File(), db: Session = Depends(get_db),
                              user: UserModel = Depends(verify_jwt)):
    if not profile_picture:
        raise HTTPException(status_code=400, detail="No file provided")
    if not profile_picture.content_type:
        raise HTTPException(status_code=400, detail="Invalid file type")
    if not profile_picture.content_type.startswith("image"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    user.profile_picture_data = await profile_picture.read()
    user.profile_picture_type = profile_picture.content_type
    user.profile_picture_name = profile_picture.filename
    db.commit()
    return user


@router.delete("/profile_picture", response_model=UserSchema)
async def delete_profile_picture(db: Session = Depends(get_db), user: UserModel = Depends(verify_jwt)):
    user.profile_picture_data = None
    user.profile_picture_type = None
    user.profile_picture_name = None
    db.commit()
    return user
