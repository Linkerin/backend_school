# Candy Delivery API
  
## About
Candy Delivery API is based on REST principles to handle information about couriers and orders, make orders' assignment, reflect completion, calculate courier's earnings amount and rating. API is based on Flask framework and created as a part of the [Yandex Backend School](https://academy.yandex.ru/schools/backend) entrance test. PostgreSQL was chosen as a database and NGINX as a proxy server.

## Server Deployment
[Docker](https://www.docker.com) containers technology was used to make the installation process of Candy Delivery API rapid and easy. To deploy the server you just have to complete a few steps:

1. Download and install Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop "Docker.com")  
For Linux users you can find the [manual here](https://hub.docker.com/search?q=&type=edition&offering=community&operating_system=linux "Docker Hub").
2. Install Docker Compose according to the guide: [https://docs.docker.com/compose/install](https://docs.docker.com/compose/install/ "Install Docker Compose").
3. Download all the files from current [GitHub repository](https://github.com/Linkerin/backend_school) to your server.
4. Inside the API folder (to move there you can use the change directory command in a terminal: `cd /your/destination/backend_school`) you should edit `.env.db` and `.env` to set your own database password and Flask secret key:  

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

   Note: NGINX server runs on port 80.  
---
If you need to stop and remove all the containers you can run this command:
```bash
sudo docker-compose down -v
```

## Documentation