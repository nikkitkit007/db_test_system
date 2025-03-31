# db_test_system
Allow make load tests for any DB


# Quiq start
## Config image connection

```
postgres: {
         "db_type": "postgresql",
         "default_user": "postgres",
         "default_password": "password",
         "default_port": 5432,
         "default_db": "test_db",
         # Зависит от того, как у вас в Dockerfile/образе обозначены переменные
         "env": {
             "POSTGRES_USER": "postgres",
             "POSTGRES_PASSWORD": "password",
             "POSTGRES_DB": "test_db",
         },
     }
```

# UI
![main_window](app_screenshots/main_window.png)
![create_scenario.png](app_screenshots/create_scenario.png)
![docker_images.png](app_screenshots/docker_images.png)
![test_results.png](app_screenshots/test_results.png)