# Basic Working KillBill Configuration

Our goal for this is to create a basic working KillBill service and configuration for the Concertim-Openstack Service. To fulling process billing metrics, complete the openstack basic configuration section. We will be linking to the official documentation wherever possible. 

## KillBill Installation

To [install KillBill](https://docs.killbill.io/latest/getting_started.html) we will use docker-compose for running the killbill services. Open a new file and use the following docker-compose:

```
version: '3.2'
volumes:
  db:
services:
  killbill:
    image: killbill/killbill:0.24.0
    ports:
      - "8080:8080"
    environment:
      - KILLBILL_DAO_URL=jdbc:mysql://db:3306/killbill
      - KILLBILL_DAO_USER=root
      - KILLBILL_DAO_PASSWORD=killbill
      - KILLBILL_CATALOG_URI=SpyCarAdvanced.xml
  kaui:
    image: killbill/kaui:2.0.11
    ports:
      - "9090:8080"
    environment:
      - KAUI_CONFIG_DAO_URL=jdbc:mysql://db:3306/kaui
      - KAUI_CONFIG_DAO_USER=root
      - KAUI_CONFIG_DAO_PASSWORD=killbill
      - KAUI_KILLBILL_URL=http://killbill:8080
  db:
    image: killbill/mariadb:0.24
    volumes:
      - type: volume
        source: db
        target: /var/lib/mysql
    expose:
      - "3306"
    environment:
      - MYSQL_ROOT_PASSWORD=killbill
```

Then run `docker-compose up`.

Once the containers are running, you should be able to access KAUI (the KillBill UI) from `http://<IP>:9090` using the `user:admin` and `password:password` credentials.

You can also go to `http://<IP>:8080/api.html` to explore the KillBill APIs.
  
You can use the following commands to check logs if something is wrong:
```
docker logs <containerid>
  
docker exec <Kill Bill Container Id> tail -f logs/killbill.out #displays Kill Bill logs
docker exec <Kaui Container Id> tail -f logs/kaui.out #displays Kaui logs
```

## Configuration of KAUI

After KillBill is up and running and KAUI is accessable, we can begin [setting up KAUI](https://docs.killbill.io/latest/quick_start_with_kaui.html).

1. Login to KAUI with `admin/password`
2. Create a new tenant when prompted using desired name, API secret and API key
3. Create a [catalog](https://docs.killbill.io/latest/userguide_subscription.html#components-catalog) or use the example in this project

With all of the above configured, you should be able to use Killbill with your Concertim-Openstack Service
