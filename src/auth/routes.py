from fastapi import APIRouter,HTTPException,status,Depends
from fastapi.responses import JSONResponse

from src.db.main import get_session
from src.db.redis import add_jti_to_blocklist
from .schemas import EmailModel, UserBooksModel, UserCreateModel,UserModel,UserLoginModel,UserResponseModel
from .service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from .utils import create_access_token, create_url_safe_token,decode_token, decode_url_safe_token,verify_password
from datetime import timedelta,datetime
from .dependencies import RefreshTokenBearer,AccessTokenBearer,get_current_user,RoleChecker
from src.errors import UserAlreadyExists,UserNotFound,InvalidCredentials,InvalidToken
from src.mail import create_message,mail
from src.config import config


auth_router=APIRouter()
user_service=UserService()
role_checker=RoleChecker(['admin','user'])
REFRESH_TOKEN_EXPIRY=2


@auth_router.post('/send_email')
async def send_email(emails:EmailModel):
    html="<h1>Welcome to our website</h1>"
    message=create_message(
        recipients=emails.addresses,
        subject="Hello",
        body=html,
    )
    await mail.send_message(message)

    return JSONResponse(content={
        "message":"Email sent successfully",
    },
    status_code=status.HTTP_200_OK
    )

@auth_router.post('/signup',status_code=status.HTTP_201_CREATED,response_model=UserResponseModel)
async def create_user_Account(user_data:UserCreateModel,session:AsyncSession=Depends(get_session)):
    email=user_data.email
    user_exists=await user_service.user_exists(email,session)

    if user_exists:
        raise UserAlreadyExists()
    
    new_user=await user_service.create_user(user_data,session)
    
    token=create_url_safe_token({'email':email})
    
    link=f"http://{config.DOMAIN}/api/v1/auth/verify/{token}"


    html_message=f"""
    <h1>Verify your email</h1>
    <p>Please click the link below to verify your email</p>
    <a href="{link}">Verify Email</a>
    """
    message=create_message(
        recipients=[email],
        subject="Verify your email",
        body=html_message,
    )
    await mail.send_message(message)



    return {
        "message":"Account created successfully! Check your email for verification",
        "user":new_user
    }


@auth_router.get('/verify/{token}')
async def verify_user_account(token:str,session:AsyncSession=Depends(get_session)):

    token_data=decode_url_safe_token(token)

    user_email=token_data.get('email')

    if user_email:
        user=await user_service.get_user_by_email(user_email,session)

        if not user:
            raise UserNotFound()
        await user_service.update_user(user,{"is_verified":True},session)

        return JSONResponse(content={
            "message":"Email verified successfully",
        },
        status_code=status.HTTP_200_OK
        )

    return JSONResponse(content={
        "message":"Error occurred while verifying email",
    },
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@auth_router.post('/login')
async def login_users(login_data:UserLoginModel,session:AsyncSession=Depends(get_session)):
    email=login_data.email
    password=login_data.password

    user= await user_service.get_user_by_email(email,session)

    if user is not None:
        password_valid=verify_password(password,user.password_hash)

        if password_valid:
            access_token=create_access_token(
                user_data={
                    'user_uid':str(user.uid),
                    'email':user.email,
                    'role':user.role
                }
            )

            refresh_token=create_access_token(
                user_data={
                    'user_uid':str(user.uid),
                    'email':user.email,
                    'role':user.role
                },
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )

            return JSONResponse(
                content={
                    'message':'Login successful',
                    'access_token':access_token,
                    'refresh_token':refresh_token,
                    "user":{
                        "email":user.email,
                        "uid":str(user.uid)
                    }
                },
                status_code=status.HTTP_200_OK
            )
        
    raise InvalidCredentials()


@auth_router.get('/refresh_token')
async def get_new_access_token(token_details:dict=Depends(RefreshTokenBearer())):
    expiry_timestamp=token_details['exp']
    # convert the expiry timestamp to datetime object
    # print(expiry_timestamp)
    if datetime.fromtimestamp(expiry_timestamp)>datetime.now():
        new_access_token=create_access_token(
            user_data=token_details['user']
        )

        return JSONResponse(content={
            "access_token":new_access_token,
        })
        
    raise InvalidToken()

@auth_router.get('/me',response_model=UserBooksModel)
async def get_current_user(user:UserModel=Depends(get_current_user),
                          _:bool=Depends(role_checker)):
    return user

@auth_router.get('/logout')
async def revoke_token(token_details:dict=Depends(AccessTokenBearer())):
    await add_jti_to_blocklist(token_details['jti'])

    return JSONResponse(content={
        "message":"Token revoked successfully",
    },
    status_code=status.HTTP_200_OK
    )
