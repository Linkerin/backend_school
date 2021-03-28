# Candy Delivery API
  
## About
Candy Delivery API is based on REST principles to handle information about couriers and orders, make orders' assignment, reflect completion, calculate courier's earnings amount and rating. API is based on Flask framework and created as a part of the [Yandex Backend School](https://academy.yandex.ru/schools/backend) entrance test.

## Server Deployment
[Docker](https://www.docker.com) containers technology was used to make the installation process of Candy Delivery API rapid and easy. To deploy the server you just have to complete a few steps:

1. Download and install Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop "Docker.com")  
For Linux users you can find the [manual here](https://hub.docker.com/search?q=&type=edition&offering=community&operating_system=linux "Docker Hub").
2. Install Docker Compose according to the guide: [https://docs.docker.com/compose/install](https://docs.docker.com/compose/install/ "Install Docker Compose").
3. Download all the files from this [GitHub repository](https://github.com/Linkerin/backend_school) to your server.
4. Inside the API folder (to move there you can use the change directory command in a terminal: `cd /your/destination/backend_school`) build docker containers using the following command:

   >`sudo docker-compose up -d --build`
5. 

sudo docker-compose exec app python manage.py create_db
sudo docker-compose down -v
`