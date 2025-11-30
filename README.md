# django-aws-model

django-aws-model is a Django app that helps you model and set up your AWS resources so that you can spend less time managing those resources and more time focusing on your applications that run in AWS.

Quick start
-----------

1. Add "aws" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "aws",
    ]

2. Run ``python manage.py migrate`` to create the models.

3. Start the development server and visit the admin to create a execution order.

4. Run the action AWS Execute
