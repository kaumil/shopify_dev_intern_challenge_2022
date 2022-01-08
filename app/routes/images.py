import logging
import os
import uuid

from aiobotocore.session import get_session
from typing import List
from fastapi import Depends, Form
from fastapi.responses import JSONResponse
from fastapi import APIRouter,status, HTTPException, File, UploadFile
from app.routes.login import get_current_active_user
from app.models.models import register_image, delete_image, make_image_public, list_images

router = APIRouter()

async def upload_image(fileobject, bucket, key):
    """
    Function to asynchronously upload image to S3

    Args:
        fileobject ([Binary Object]): [Image Data]
        bucket ([str]): [Destination bucket]
        key ([str]): [Key of the target destination]

    Raises:
        HTTPException: [500 Internal Server Error if there's an error uploading the image]

    Returns:
        [None]: [No file output except errors]
    """
    session = get_session()
    region = os.environ.get("REGION")
    async with session.create_client('s3', region_name=region, endpoint_url=os.environ.get("path"),
                                        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                                        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID")) as client:
        file_upload_response = await client.put_object(ACL="private", Bucket=bucket, Key=key, Body=fileobject)

        if file_upload_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            key_str = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
            logging.info(f"File uploaded path : {key_str}")
            return key_str
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error uploading image"
    )

@router.get('/show_images',status_code=status.HTTP_200_OK)
def show_deleted_images(token=Depends(get_current_active_user)):
    images = list_images(user_id=token.user_id,is_deleted=False)
    return JSONResponse(content={"images":images},status_code=status.HTTP_200_OK)

@router.get('/show_deleted_images',status_code=status.HTTP_200_OK)
def show_deleted_images(token=Depends(get_current_active_user)):
    images = list_images(user_id=token.user_id,is_deleted=True)
    return JSONResponse(content={"images":images},status_code=status.HTTP_200_OK)

@router.get('/delete_image',status_code=status.HTTP_200_OK)
def delete_images(image_id, token=Depends(get_current_active_user)):
    delete_image(image_id=image_id)
    return JSONResponse(content={"msg":"Image deleted"},status_code=status.HTTP_200_OK)

@router.get('/share_image',status_code=status.HTTP_201_CREATED)
def share_image_url(image_id,token=Depends(get_current_active_user)):
    public_url = make_image_public(image_id=image_id)
    return JSONResponse(content={"image_public_url":f"{public_url}"},status_code=status.HTTP_200_OK)


@router.post('/upload_images',status_code=status.HTTP_201_CREATED)
async def upload_images(images: List[UploadFile]= File(...),token=Depends(get_current_active_user)):
    print("Arrived")
    username = token.username
    try:
        for image in images:
            split_file_name = os.path.splitext(image.filename)
            file_extension = split_file_name[1]
            key_str = await upload_image(image.file._file,bucket=os.environ.get("bucketname"),key=str(uuid.uuid4())+file_extension)
            register_image(username,key_str)

        return JSONResponse(content={"msg":"Images uploaded"},status_code=status.HTTP_200_OK)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while uploading images"
        )
    
