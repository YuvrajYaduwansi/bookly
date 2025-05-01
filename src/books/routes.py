
from fastapi import APIRouter,HTTPException,status,Depends
from typing import List

# from src.books.book_data import books
from src.books.schemas import Book, BookDetailModel, BookUpdateModel,BookCreateModel
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.service import BookService
from src.auth.dependencies import AccessTokenBearer,RoleChecker


book_router=APIRouter()
book_service=BookService()
access_token_bearer=AccessTokenBearer()
role_checker=RoleChecker(['admin','user'])
# user_details=Depends(access_token_bearer) helps protect the route so when we pass bearer token it will be decoded and user details will be returned

# ,dependencies=[Depends(role_checker)] is a different way to inject dependencies into the route

@book_router.get('/',response_model=List[Book],dependencies=[Depends(role_checker)])
async def get_all_books(session:AsyncSession=Depends(get_session),token_details:dict=Depends(access_token_bearer)):
    return await book_service.get_all_books(session)


@book_router.get('/user/{user_uid}',response_model=List[Book],dependencies=[Depends(role_checker)])
async def get_user_book_submissions(user_uid:str,session:AsyncSession=Depends(get_session),token_details:dict=Depends(access_token_bearer)):
    return await book_service.get_user_books(user_uid,session)


@book_router.post('/',status_code=status.HTTP_201_CREATED,response_model=Book,dependencies=[Depends(role_checker)])
async def create_a_book(book_data:BookCreateModel,session:AsyncSession=Depends(get_session),token_details:dict=Depends(access_token_bearer))->dict:
    user_id=token_details.get('user')['user_uid']
    return await book_service.create_book(book_data,user_id,session)


@book_router.get('/{book_uid}',response_model=BookDetailModel,dependencies=[Depends(role_checker)])
async def get_book(book_uid:str,session:AsyncSession=Depends(get_session),token_details:dict=Depends(access_token_bearer))->dict:
    book= await book_service.get_book(book_uid,session)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Book not found")
    return book


@book_router.put('/{book_uid}',response_model=Book,dependencies=[Depends(role_checker)])
async def update_book(book_uid:str,update_data:BookUpdateModel,session:AsyncSession=Depends(get_session),token_details:dict=Depends(access_token_bearer))->dict:
    updated_book= await book_service.update_book(book_uid,update_data,session)
    if updated_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Book not found")
    return updated_book



@book_router.delete('/{book_uid}',dependencies=[Depends(role_checker)])
async def delete_book(book_uid:str,session:AsyncSession=Depends(get_session),token_details:dict=Depends(access_token_bearer))->dict:
    deleted_book= await book_service.delete_book(book_uid,session)
    if deleted_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Book not found")
    return {}
     