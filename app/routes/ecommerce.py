from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi import APIRouter,status
from app.routes.login import get_current_active_user, get_current_active_seller
from app.models.models import query_user, list_marketplace_images, sell_user_image, buy_user_image

router = APIRouter()

@router.get("/register_seller",status_code=status.HTTP_201_CREATED)
def register_seller(token=Depends(get_current_active_user)):
    user = query_user(token.username)
    user.role = "seller"
    user.save()
    return JSONResponse(content={"msg":"User status changed to seller"},status_code=status.HTTP_201_CREATED)

@router.get("/list_seller_images",status_code=status.HTTP_200_OK)
def list_seller_images(username,token=Depends(get_current_active_user)):
    seller_images = list_marketplace_images(username)
    return JSONResponse(content={"images":seller_images},status_code=status.HTTP_200_OK)


@router.get("/sell_image",status_code=status.HTTP_201_CREATED)
def sell_image(image_id,price,seller=Depends(get_current_active_seller)):
    marketplace_id = sell_user_image(image_id,price,seller)
    return JSONResponse(content={"msg":f"Image uploaded to marketplace.Marketplace id: {marketplace_id}"},status_code=status.HTTP_201_CREATED)
    

@router.get("/buy_image",status_code=status.HTTP_201_CREATED)
def buy_image(marketplace_id,user=Depends(get_current_active_user)):
    marketplace_id,transaction_id = buy_user_image(marketplace_id,user)
    return JSONResponse(content={"msg":f"Image bought.Ownership transferred. Marketplace id: {marketplace_id}. Transaction id:{transaction_id}"},status_code=status.HTTP_201_CREATED)
