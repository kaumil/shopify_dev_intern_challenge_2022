import os
import logging
from datetime import datetime
import boto3
from boto3 import Session
from botocore.session import get_session
from uuid import uuid4
from fastapi import status
from fastapi.exceptions import HTTPException
from pynamodb.models import Model
from pynamodb.indexes import LocalSecondaryIndex, GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import BooleanAttribute, NumberAttribute, UnicodeAttribute, UTCDateTimeAttribute, UnicodeSetAttribute

class Users(Model):
    """
    Dynamodb class to represent users on the image repo site

    Args:
        Model ([PynamoDB Model]): [PynamoDB BaseClass]
    """
    class Meta:
        table_name = "Users"
        region = "us-east-1"
        write_capacity_units = 10
        read_capacity_units = 10
        host = "http://localhost:4566"
    
    user_id = UnicodeAttribute()
    username = UnicodeAttribute(hash_key=True)
    password = UnicodeAttribute()
    last_logged_in = UTCDateTimeAttribute()
    role = UnicodeAttribute()
    disabled = BooleanAttribute(default=False)
    credit = NumberAttribute(default=0)
    debit = NumberAttribute(default=0)

class Images(Model):
    """
    Dynamodb class to represent images on the image repo site

    Args:
        Model ([PynamoDB Model]): [PynamoDB BaseClass]
    """
    class Meta:
        table_name = "Images"
        region = "us-east-1"
        write_capacity_units = 10
        read_capacity_units = 20
        host = "http://localhost:4566"
    
    imageid = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)
    is_public = BooleanAttribute(default=False)
    tags = UnicodeSetAttribute(null=True)
    public_url = UnicodeAttribute(null=True)
    uploaded_on = UTCDateTimeAttribute()
    is_deleted = BooleanAttribute(default=False)
    


class MarketplaceSellerIndex(GlobalSecondaryIndex):
    """
    Index to view items by seller name

    Args:
        GlobalSecondaryIndex ([PynamoDB GlobalSecondaryIndex]): [PynamoDB base secondary index]
    """
    class Meta:
        read_capacity_units = 2
        write_capacity_units = 1
        projection = AllProjection()
    seller_name = UnicodeAttribute(hash_key=True)

class Marketplace(Model):
    """
    DynamoDB class to represent marketplace item on the image repo site

    Args:
        Model ([PynamoDB Model]): [PynamoDB BaseClass]
    """
    class Meta:
        table_name = "Market"
        region = "us-east-1"
        write_capacity_units = 10
        read_capacity_units = 20
        host = "http://localhost:4566"
    
    marketplace_id = UnicodeAttribute(hash_key=True)
    image_id = UnicodeAttribute()
    seller_id = UnicodeAttribute()
    seller_name = UnicodeAttribute()
    buyer_id = UnicodeAttribute(null=True)
    buyer_name = UnicodeAttribute(null=True)
    image_public_url = UnicodeAttribute()
    image_price = NumberAttribute()
    transaction_id = UnicodeAttribute(null=True)
    sold = BooleanAttribute(default=False)
    sold_on = UTCDateTimeAttribute(null=True)
    seller_index = MarketplaceSellerIndex()
    
    
    

def query_user(username):
    """
    Function to query username on Users and return a user if existed

    Args:
        username ([str]): [String of the username]

    Returns:
        [User Object]: [User Object Item]
    """
    result = list(Users.query(username))
    if result:
        return result[0]
    else:
        return None

def create_user(data,role="user"):
    """
    Function to create a User object

    Args:
        data ([dict]): [Dictionary containing the data of the user]
        role (str, optional): [Role of the newly created user. Currently allowed values are 'user','admin' and 'seller']. Defaults to "user".

    Returns:
        [bool]: [Validation if user was successfully created]
    """
    user = Users(data['key'],user_id=str(uuid4()),password=data['password'],last_logged_in=datetime.now(),role=role)
    user.save()
    return True

def register_image(username,key_str):
    """
    Function to register a stored image to a particular user

    Args:
        username ([str]): [Username of the owner of the image]
        key_str ([str]): [URL of the image uploaded to S3]

    Returns:
        [Bool]: [Validation if image was successfully registered]
    """
    user = query_user(username)
    image_id = str(uuid4())
    image = Images(imageid=image_id,user_id=user.user_id,uploaded_on=datetime.now(),public_url=key_str)
    image.save()
    print(f"Image ID: {image_id}")
    print(f"Image uploaded: {key_str}")
    return True

def delete_image(image_id):
    """
    Function to delete image given the image_id

    Args:
        image_id ([uuid4]): [Unique id of the image to be deleted]

    Returns:
        [Bool]: [Validation if image ws successfully registered]
    """
    image = list(Images.query(image_id))[0]
    if image:
        image.is_deleted = True
        image.save()
        return True
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image not found"
        )


def list_images(user_id,is_deleted):
    """
    Function to list images by a certain user. If is_deleted is True, the function will return the deleted images, else it will show the current images

    Args:
        user_id ([uuid4]): [Unique user_id]
        is_deleted (bool): [Is the requirement to list deleted images or not]

    Returns:
        [List]: [List of the public urls were each image is hosted on S3]
    """

    print(
        list(
            Images.scan((Images.user_id==user_id)&(Images.is_deleted==is_deleted))
        )
    )
    # print(list(Images.scan(Images.user_id==user_id),Images.is_deleted==is_deleted)))
    images = [image.public_url for image in Images.scan((Images.user_id==user_id)&(Images.is_deleted==is_deleted))]
    print([image.imageid for image in Images.scan((Images.user_id==user_id)&(Images.is_deleted==is_deleted))])
    return images

def make_image_public(image_id):
    """
    Function to make a

    Args:
        image_id ([type]): [description]

        Image s3 url example: https://imagerepobucket.s3.us-east-1.amazonaws.com/2bc3c8dc-359a-4c19-bbbe-0ad9c33b8edf.jpg

    Returns:
        [Image public url]: [Public url of the image]
    """
    image = list(Images.query(image_id))[0]

    vals = image.public_url.split('/')
    domain,src_key = vals [-2], vals[-1]
    bucket = domain.split('.')[0]
    session = Session()
    
    region = os.environ.get("REGION")
    client = session.client('s3', region_name=region, endpoint_url=os.environ.get("path"),
                                        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                                        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"))

        
    client.put_object_acl(
        ACL='public-read',
        Bucket=bucket,
        Key=src_key
    )

    image.is_public = True
    image.save()
    return image.public_url

def list_marketplace_images(username):
    """
    Function to list all the marketplace images from a particular seller

    Args:
        username ([str]): [Username of the seller]

    Returns:
        [list]: [List of all the public urls of the images]
    """
    images = [image.image_public_url for image in Marketplace.seller_index.query(username)]
    return images

def sell_user_image(image_id,price,seller):
    """
    Function to upload image to the marketplace

    Args:
        image_id ([uuid4]): [Unique image id]
        price ([Int]): [Price of the image]
        seller ([uuid4]): [Unique seller id]

    Returns:
        [type]: [description]
    """
    marketplace_id = str(uuid4())
    image = list(Images.query(image_id))[0]
    image_public_url = make_image_public(image_id)

    marketplace_item = Marketplace(marketplace_id,image_id=image.imageid,seller_id=seller.user_id,seller_name=seller.username,image_public_url=image_public_url,image_price=int(price))
    marketplace_item.save()

    return marketplace_id

def buy_user_image(marketplace_id,user):
    """
    Function to buy an image

    Args:
        marketplace_id ([uuid4]): [Unique marketplace id]
        user ([uuid4]): [Unique buyer id]

    Raises:
        HTTPException: [401 Unauthorized if image is already bought]
        HTTPException: [401 Unauthorized if buyer and the seller are the same]

    Returns:
        [MarketplaceID, TransactionID]: [uuids of the unique marketplace item id and transaction id]
    """
    marketplace_item = list(Marketplace.query(marketplace_id))[0]
    seller = list(Users.query(marketplace_item.seller_name))[0]
    image_id = marketplace_item.image_id

    if marketplace_item.sold:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Image already sold"
        )

    if marketplace_item.seller_id == user.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A user cannot buy their own image"
        )
    marketplace_item.buyer_id = user.user_id
    marketplace_item.buyer_name = user.username

    transaction_id = str(uuid4())
    marketplace_item.transaction_id = transaction_id
    marketplace_item.sold = True
    marketplace_item.sold_on = datetime.now()
    value = marketplace_item.image_price
    user.debit -= value
    seller.credit += value


    #changing ownership of the image
    image = list(Images.query(image_id))[0]
    image.user_id = user.user_id

    user.save()
    seller.save()
    marketplace_item.save()
    image.save()

    print(seller.credit,seller.debit,user.credit,user.debit)
    return marketplace_id, transaction_id