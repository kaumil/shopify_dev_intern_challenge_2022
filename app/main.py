import logging
from .logger import CustomizeLogger
import os
import uvicorn

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from mangum import Mangum

from app.routes import ecommerce, login, images

from app.handlers.exception_handler import exception_handler
from app.handlers.http_exception_handler import http_exception_handler



#Loading the env variables
load_dotenv(".env")

#Initializing FastAPI object
app = FastAPI(title="ImageRepo",debug=False)


#Logging Config
logger = logging.getLogger(__name__)
basedir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(basedir, ("logging_config.json"))



# adding logging to the application
logger = CustomizeLogger.make_logger(basedir, config_path)
app.logger = logger



#Exception handlers
app.add_exception_handler(Exception, exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


#LoginManager


#Routers go here
app.include_router(login.router, tags=['login'])
app.include_router(images.router,tags=['images'])
app.include_router(ecommerce.router,tags=['marketplace'])

#Handlers for AWS Lambda
handler = Mangum(app)



#Self contained application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)