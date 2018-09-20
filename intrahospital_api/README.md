## Intrahospital Api

This provide all services to query from upstream within the hospital.

#### Basic Overview

The intrahospital api is a framework for many different `service`.

A `service` is an upstream resource regarding a certain type of information for example lab tests or demographics.

Each service is independent but shares a common structure. Its a directory with the public functions exposed in the `__init__.py`.

It has a file called `service.py` this handles the interaction between the backend and your models.

It has a directory called `backends` this contains `live.py` and `dev.py`. `live.py` will be used in production, `dev.py` will be used in dev. Which is used is defined by `settings.API_STATE`.


#### How do you write a new service.

Your new service should be of be structured

```
    { service_name } /
        __init__.py # put you public functions in here
        service.py # put your model interations in here

        backends /
            live.py # put an object called `Api` in here its for your live db interactions
            dev.py # put an object called `Api` in here its for your dev interactions.

```

To get your backend you can use `intrahospital_api.base.service_utils.get_api({{ service_name }})`

When saving your models you should use the api user. This can be got from `intrahospital_api.base.service_utils.get_user()`



