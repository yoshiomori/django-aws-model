from django.views import generic
from django.shortcuts import render

from .models import Service


class DefaultConfigurationJSView(generic.ListView):
    model = Service
    template_name = 'aws/default-configuration.js'
    content_type = 'text/javascript'
