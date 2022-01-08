from fastapi import HTTPException
import os, boto3
from botocore.exceptions import ClientError
from app.models.models import Marketplace, Users, Images
from os import EX_PROTOCOL, environ, wait
from datetime import datetime


AWS_REGION = 'us-east-1'
AWS_PROFILE = 'sfuuser'
ENDPOINT_URL = os.environ.get("path")
print(ENDPOINT_URL)

boto3.setup_default_session(profile_name=AWS_PROFILE)

s3_client = boto3.client("s3", region_name=AWS_REGION,
                         endpoint_url=ENDPOINT_URL)

def set_config():
    """Picks up the settings from the config files and automatically decides between using Local vs AWS DynamoDB"""
    if environ.get("service") == 'docker':
        print("Running with Local DynamoDB...")
        db_path = environ.get("path") or None
        Users.Meta.host = db_path
        Images.Meta.host = db_path
    else:
        print("Running with AWS DynamoDB using the credentials in the .env file...")

def setup_boto():
    global endpoint_url, s3_client, aws_region, aws_profile
    endpoint_url = os.environ.get("path")
    aws_profile = os.environ.get("awsprofile")
    aws_region = os.environ.get("REGION")


    boto3.setup_default_session(profile_name=aws_profile)

    s3_client = boto3.client("s3", region_name=aws_region,endpoint_url=endpoint_url)


def create_bucket(bucket_name):
    """
    Creates a S3 bucket.
    """
    try:
        global s3_client
        response = s3_client.create_bucket(
            Bucket=bucket_name)
    except ClientError:
        raise HTTPException('Could not create S3 bucket locally.')
    else:
        return response

def sanity_check():
    set_config()

    setup_boto()
    if not Users.exists():
        print("User Table does not exist, creating one...")
        Users.create_table(read_capacity_units=10, write_capacity_units=10, wait=True)

        print("Adding user to the table...")
        user = Users(user_id=0, username="admin",password="$2b$12$vHRcrvBJc7ZoYB/K8q3QDeLjJPjBvK5D4lkez8CdVL.TlEC/mYZhy",last_logged_in=datetime.now(),role="admin")
        user.save()

        print("Selecting users from User Table...")
        stored_user = Users.get("admin")
        print(stored_user)

        print("Scanning users from User Table...")
        for user in Users.scan(Users.username == "admin"):
            print(user)
        print("Exiting...")

    print("Creating Bucket")
    create_bucket("imagerepobucket")
    print("bucket created")
    
    if not Images.exists():
        print("Images Table does not exist, creating one...")
        Images.create_table(read_capacity_units=10,write_capacity_units=10,wait=True)
    
    if not Marketplace.exists():
        print("Marketplace Table does not exist, creating one...")
        Marketplace.create_table(read_capacity_units=10,write_capacity_units=10,wait=True)
