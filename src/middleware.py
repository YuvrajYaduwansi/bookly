from fastapi import FastAPI,Request,status
import time
import logging
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logger=logging.getLogger('uvicorn.access')
logger.disabled=True


def register_middleware(app:FastAPI):


    @app.middleware("http")
    async def custom_logging(request:Request,call_next):
        start_time=time.time()
      
        response=await call_next(request)
        
        process_time=time.time()-start_time
        message = f"{request.client.host}:{request.client.port} - {request.method} - {request.url.path} - {response.status_code} completed after {process_time}s"


        print(message)

        return response


    app.add_middleware(CORSMiddleware,
                       allow_origins=["*"],
                       allow_credentials=True,
                       allow_methods=["*"],
                       allow_headers=["*"],
                       )

    app.add_middleware(TrustedHostMiddleware,allowed_hosts=["localhost","127.0.0.1"])
# just sample to see it can be done with middleware but we already did it with dependency injection
    # @app.middleware("http")
    # async def authorization(request:Request,call_next):
    #     if not "Authorization" in request.headers:
    #         return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,content={"message":"Not authorized","resolution":"Provide valid creds to proceed"})
        
    #     response=await call_next(request)
    #     return response
