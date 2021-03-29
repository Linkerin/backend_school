# Candy Delivery API

## Contents
[About](#about)  
[Server Deployment](#deploy)  
[Routings](#routings)

   * [/couriers](#couriers)  
   * [/couriers/$courier_id](#couriers-id)  
   * [/orders](#orders)  
   * [/orders/assign](#orders-assign)  
   * [/orders/complete](#orders-complete)

[Requirements](#requirements)  


## About <a id="about"></a>
Candy Delivery API is based on REST principles to handle information about couriers and orders, make orders' assignment, reflect completion, calculate courier's earnings amount and rating. API is based on Flask framework and created as a part of the [Yandex Backend School](https://academy.yandex.ru/schools/backend) entrance test. [PostgreSQL](https://www.postgresql.org) was chosen as a database, [NGINX](https://www.nginx.com) as a proxy server and [Gunicorn](https://gunicorn.org) as WSGI HTTP Server.

## Server Deployment <a id="deploy"></a>
[Docker](https://www.docker.com) containers technology was used to make the installation process of Candy Delivery API rapid and easy. To deploy the server you just have to complete a few steps:

1. Download and install Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop "Docker.com")  
For Linux users you can find the [manual here](https://hub.docker.com/search?q=&type=edition&offering=community&operating_system=linux "Docker Hub").
2. Install Docker Compose according to the guide: [https://docs.docker.com/compose/install](https://docs.docker.com/compose/install/ "Install Docker Compose").
3. Download all the files from current [GitHub repository](https://github.com/Linkerin/backend_school) to your server and go inside the folder using terminal:

   ```bash
   git clone https://github.com/Linkerin/backend_school.git
   cd /your/destination/backend_school
   ```

4. Inside the API folder you should edit `.env.db` and `.env` to set your own database password and Flask secret key:  

   .env.db
   ```python
   # Change POSTGRES_PASSWORD
   POSTGRES_USER=flask_admin
   POSTGRES_PASSWORD=your_secret_password
   POSTGRES_DB=candy_delivery
   ```

   .env
   ```python
   # Change SECRET_KEY
   FLASK_APP=app/__init__.py
   FLASK_RUN_HOST=0.0.0.0
   FLASK_ENV=production
   SECRET_KEY='YOUR_SECRET_KEY'
   # POSTGRES_PASSWORD from .env.db instead of 'your_secret_password'
   DATABASE_URL='postgresql://flask_admin:your_secret_password@flaskapp_postgres:5432/candy_delivery'
   ```

   `SECRET_KEY` is used for securely signing the session cookie and other security reasons. There are several methods how you can get a long random string and here is one of them using Python:  
   ```python
   import secrets


   key = secrets.token_hex(16)
   print(f'Your secret key is {key}')

   # Example output: Your secret key is 35a72ed52d040d3f466d34a93315b5f6
   ```

5. Build docker containers using the following command:

   ```bash
   sudo docker-compose up -d --build
   ```

6. After that you should create tables in the database:

   ```bash
   sudo docker-compose exec app python manage.py create_db
   ```

7. That's it! Now everything should be working just fine. Test it out connecting to your server IP address. You will see the following message:  
   > Candy Delivery App API

   Note: NGINX server runs on port 80, Flask application itself on port 8080.  
---
If you need to stop and remove all the containers you can run this command:
```bash
sudo docker-compose down -v
```

## Routings <a id="routings"></a>

* ### /couriers <a id="couriers"></a>
   Input: **JSON**  
   Allowed methods: **POST**  
   Response options:  
   * HTTP 201 Created
   * HTTP 400 Bad Request
   * HTTP 405 Method Not Allowed

   This routing is used to create information about the couriers. It receives a JSON with obligatory fields and in case of successful validation creates couriers in the database and returns a JSON with a list of created couriers' IDs.
   
   Example:
   ```json
   POST /couriers
   {
      "data": [
         {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
         }
      ]
   }
   ```

   Sucessful creation response:
   ```json
   HTTP 201 Created
   {
      "couriers": [{"id": 1}]
   }
   ```

   For example, if the courier was already created the response will be the following:
   ```json
   HTTP 400 Bad Request
   {
      "Errors": [
         {"id 1": "id already exists"}
     ],
      "validation error": {
         "couriers": [
            {"id": 1}
         ]
      }
   }
   ```

   Fields description:

   | Field         | Type                       | Description                                                     |
   | ------------- |--------------------------- | --------------------------------------------------------------- |
   | courier_id    | Integer, positive          | Unique courier's ID                                             |
   | courier_type  | String                     | Possible values: 'foot', 'bike', 'car'                          |
   | regions       | Array of positive integers | List of regions' IDs where a courier can work                   |
   | working_hours | Array of strings           | Courier's work schedule in the following format: `"HH:MM-HH:MM"` |

   Courier's load capacity depends on his type:  
   * foot - 10 kg;
   * bike - 15 kg;
   * car - 50 kg.

* ### /couriers/$courier_id <a id="couriers-id"></a>
   Input: **JSON**  
   Allowed methods: **PATCH**, **GET**  
   Response options:  
   * HTTP 200 OK
   * HTTP 400 Bad Request
   * HTTP 404 Not Found
   * HTTP 405 Method Not Allowed

   This routing is used to change the courier's information and accepts JSON with any fields from the list: `courier_type`, `regions`, `working_hours`. Additional properties are not allowed: in this case the server will return `HTTP 400 Bad Request` response.  
   Keep in mind that the change of courier's attributes will affect the set of orders already assigned to him. For example, if you change `courier_type` (which means you change his load capacity) total weight of all uncompleted couriers's assigned orders will be recalculated and exceeding orders will become available for assignment.  
   Data format requirements are the same as for `/couriers` routing.

   `GET` method for this routing returns courier's information. It also returns his rating and total earnings if the courier had at least one completed orders assignment.

   Example:
   ```json
      PATCH /couriers/1
      {
         "courier_type": "bike"
      }
   ```

   Successful update response:
   ```json
   HTTP 200 OK
      {
         "courier_id": 1,
         "courier_type": "bike",
         "regions": [1, 12, 22],
         "working_hours": ["11:35-14:05", "09:00-11:00"]
      }
   ```

   Attempt to update a non-existent courier:
   ```json
   PATCH /couriers/200
      {
         "regions": [7, 23, 78],
         "working_hours": ["08:00-17:00"]
      }
   ```
   And the response wil be `HTTP 404 Not Found`.

   ---

   `GET` request example:
   ```json
   GET /couriers/1
      {
        "courier_id": 1,
        "courier_type": "bike",
        "earnings": 2500,
        "rating": 1.72,
        "regions": [1, 12, 22],
        "working_hours": ["11:35-14:05", "09:00-11:00"]
      }
   ```

* ### /orders <a id="orders"></a>
   Input: **JSON**  
   Allowed methods: **POST**  
   Response options:  
   * HTTP 201 Created
   * HTTP 400 Bad Request
   * HTTP 405 Method Not Allowed

   This routing is used to create information about the orders. It receives a JSON with obligatory fields and in case of successful validation creates orders in the database and returns a JSON with a list of created orders' IDs.

   Example:
   ```json
   POST /orders
   {
      "data": [
         {
            "order_id": 1,
            "weight": 0.23,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
         }
      ]
   }
   ```

   Sucessful creation response:
   ```json
   HTTP 201 Created
   {
      "orders": [{"id": 1}]
   }
   ```

   Fields description:

   | Field          | Type                                  | Description                                                                       |
   | -------------- |-------------------------------------- | --------------------------------------------------------------------------------- |
   | order_id       | Integer, positive                     | Unique order's ID                                                                 |
   | weight         | Number, precision: 2 digits, positive | Order's weight should be greater than or equal to 0.01 and less than or equal to 50 |
   | region         | Integer, positive                     | List of regions' IDs where a courier can work                                     |
   | delivery_hours | Array of strings                      | Time periods when the customer can accept the delivery in the following format: `"HH:MM-HH:MM"` |

   And here is an example of invalid `"region"` field type:
   ```json
   POST /orders
   {
      "data": [
         {
            "order_id": 258,
            "weight": 29.7,
            "region": "1",
            "delivery_hours": ["09:00-18:00"]
         }
      ]
   }
   ```

   Response:

   ```json
   HTTP 400 Bad Request
   {
      "Errors": [
         {"id 258": "{'region': ['Not a valid integer.']}"}
      ],
      "validation error": {
         "orders": [
            {"id": 258}
         ]
      }
   }
   ```

   * ### /orders/assign <a id="orders-assign"></a>
   Input: **JSON**  
   Allowed methods: **POST**  
   Response options:  
   * HTTP 200 OK
   * HTTP 400 Bad Request
   * HTTP 405 Method Not Allowed

   This routing is used to assign orders to a courier. The routing accepts only `"courier_id"` property inside JSON with a valid ID. In case of successful assignment the server will return a JSON containing a list of assigned orders and assign time in ISO 8601 format. If there are no available orders for this courier, the server will return only an empty list of order IDs without `"assign_time"` property.

   POST example:

   ```json
   POST /orders/assign
   {
      "courier_id": 2
   }
   ```

   Response:

   ```json
   HTTP 200 OK
      {
         "assign_time": "2021-03-29T11:18:03.496970+00:00",
         "orders": [{"id": 1}, {"id": 2}, {"id": 3}]
      }
   ```

   If you make a `POST` request for the courier who already has assigned orders you will receive information about his orders that are currently uncomleted in the same JSON format.

   * ### /orders/complete <a id="orders-complete"></a>
   Input: **JSON**  
   Allowed methods: **POST**  
   Response options:  
   * HTTP 200 OK
   * HTTP 400 Bad Request
   * HTTP 405 Method Not Allowed

   This routing is used for sending the order completion information. JSON should include valid `"courier_id"`, `"order_id"` and `"complete_time"` in ISO 8601 or RFC 3339 format. The order couldn't be completed before its' assign time or before the completion time of the previous order delivered by the courier. If everything is correct, the server will return an order ID.
   Keep in mind that the order should be assigned to the courier stated in the `"courier_id"` field.

   POST example:

   ```json
   POST /orders/assign
   {
      "courier_id": 2,
      "order_id": 1,
      "complete_time": "2021-03-29T11:44:03.31Z"
   }
   ```

   Response:

   ```json
   HTTP 200 OK
      {
         "order_id": 1
      }
   ```

   If now you make a `POST` request containing `{"courier_id": 2}` to `/orders/assign` routing, you will see that *order_id 1* was removed from the response:

   ```json
   HTTP 200 OK
      {
         "assign_time": "2021-03-29T11:18:03.496970+00:00",
         "orders": [{"id": 2}, {"id": 3}]
      }
   ```

   ## Requirements <a id="requirements"></a>

   In case you want to start a Flask app without deploying it using Docker all the required pip packages are listed in the [requirements.txt](https://github.com/Linkerin/backend_school/blob/main/requirements.txt) inside this repository.