# shopify_dev_intern_challenge_2022
Submission for the Shopify Dev Intern Challenge 2022

###### Hi there :) Kaumil here. This is my shot at making an image repository using FastAPI and AWS Services(DynamoDB and S3).

#### Features Implemented:
- User Login and Sign up system, with different roles for future prospects to make admin panel
- User can upload multiple images. Each image is private by default and only the user can access them
- User can delete images. Furthermore, images can be shared by making them public
- Marketplace for buying and selling images. 
- User can register themselves as sellers
- Each seller can choose which image to sell from their repo
- Money is registered as a simple credit-debit system for each user

#### Configuration Steps:
- After cloning the git repo, create a virtualenv to avoid dependency conflicts
- This project depends on localstack for development, and hence localstack has to be initialized using `localstack start -d`
- On the root level of the repo, start the project using `uvicorn app.main:app --reload`
- Go to `http://127.0.0.1:8000/docs` to access all the api endpoints. Click on the `/sanity_check` endpoint which creates all the necessary tables
- Authorize yourself by clicking on the green Authorize button on top right with credentials: `username: admin password: admin`
- Create users using `/signup` functionality with the username and password of your choice. <b>Usernames are unique</b>
- Login to your account with your username and password
- Upload an image using `/upload_images` api which allows for multiple files
- `/show_images` to show the urls of the images
- `/delete_image` to delete a particular image. Image ID is required which is printed on the console when images are uploaded. The logic behind this is that the frontend framework will provide the Image ID required for the system to run.
- `/share_image` to make an image public and get its public url. Image ID is required
- `/register_seller` After logging in, a user can register themselves as seller
- `/list_seller_images` Provide a seller's username and this will provide all the images listed by that seller
- `/sell_image` Image ID required and desirable selling price of the image required. Marketplace Item ID would be generated.
- `/buy_image` Marketplace Item ID required. After this the buyer would be transferred as the owner of the image. A person cannot buy their own image or buy an already bought image. This endpoint would return the marketplace item id and transaction id.