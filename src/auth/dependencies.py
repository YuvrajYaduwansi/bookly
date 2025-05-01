from fastapi import Request,HTTPException,status,Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from .utils import decode_token
from src.db.redis import token_in_blocklist
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import UserService
from typing import List,Any
from src.db.models import User

user_service=UserService()

class TokenBearer(HTTPBearer):
    def __init__(self,auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self,request:Request)->HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)
# creds.sceheme = Bearer
        print(creds.scheme)
# creds.credentials = token value  like eyaefaefa273fvahfj
        print(creds.credentials)
# we are returning the credentials so that we can use it to decode the token
        token=creds.credentials
        token_data=decode_token(token)
        
        if not self.token_valid(token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail={"error":"Invalid or expired token",
            "resolution":"Please get a new token"
            })
        
        if await token_in_blocklist(token_data['jti']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail={"error":"Token is invalid or revoked",
            "resolution":"Please get anew token"
            })

        self.verify_token_data(token_data)

        return token_data
    
    def token_valid(self,token:str)->bool:
        

        token_data=decode_token(token)

        return token_data is not None
        # easy way to do it
        # return True if token_data is not None else False
        
        # if token_data is not None:
        #     return True
        # else:
        #     return False

    def verify_token_data(self,token_data:dict)->dict:
        raise NotImplementedError('Please override this method in the child class')
        
class AccessTokenBearer(TokenBearer):
    def verify_token_data(self,token_data:dict)->None:
        if token_data and token_data['refresh']:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Please provide an access token')

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self,token_data:dict)->None:
        if token_data and not token_data['refresh']:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Please provide an refresh token')
        

async def get_current_user(token_details:dict=Depends(AccessTokenBearer()),
session:AsyncSession=Depends(get_session)):

    user_email=token_details['user']['email']

    user=await user_service.get_user_by_email(user_email,session)

    return user

class RoleChecker:
    def __init__(self,allowed_roles:List[str])->None:
        self.allowed_roles=allowed_roles

    def __call__(self,current_user:User=Depends(get_current_user))->Any:

        if current_user.role in self.allowed_roles:
            return True
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail='You are not alowed to perform this action')

