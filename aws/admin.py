import builtins

from boto3 import client
from django.contrib import admin
from django.contrib import messages
from django.forms.widgets import Script

from .models import AccessKey, Service, Configuration, ValueType, Name, Method, DefaultConfiguration, ExecutionOrder, Closure, Response, PackageName, ConfigurationPackage, DefaultConfigurationPackage


class AccessKeyAdmin(admin.ModelAdmin):
    list_display = ["id", "access_key_id"]


class ConfigurationInline(admin.StackedInline):
    model = Configuration
    extra = 1

    class Media:
        js = [Script("/aws/default-configuration.js")]


class DefaultConfigurationInline(admin.StackedInline):
    model = DefaultConfiguration
    extra = 1


class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "method"]
    search_fields = ["name__value"]
    inlines = [DefaultConfigurationInline]


class ConfigurationPackageInline(admin.StackedInline):
    model = ConfigurationPackage
    extra = 1


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ["pk", "closure", "key", "value"]
    inlines = [ConfigurationPackageInline]


class DefaultConfigurationPackageInline(admin.StackedInline):
    model = DefaultConfigurationPackage
    extra = 1


class DefaultConfigurationAdmin(admin.ModelAdmin):
    list_display = ["id", "service", "key", "value"]
    inlines = [DefaultConfigurationPackageInline]


class BucketDataAdmin(admin.ModelAdmin):
    list_display = ["id", "location"]

class ClosureInline(admin.StackedInline):
    model = Closure


class ExecutionOrderAdmin(admin.ModelAdmin):
    inlines = [ClosureInline]
    actions = ["aws_execute"]

    @admin.action(description="AWS Execute")
    def aws_execute(self, request, queryset):
        for execution_order in queryset:
            env_var = {}
            for closure in execution_order.closure_set.all():
                service_name = str(closure.service.name)
                service = client(service_name)
                method_kwargs = {
                    configuration.key: configuration.get_value(env_var)
                    for configuration in closure.configuration_set.all()
                }
                value = getattr(service, str(closure.service.method))(**method_kwargs)
                if closure.variable_name:
                    env_var[closure.variable_name] = value
                response = Response()
                response.value = value
                response.save()
                closure.service.response = response
                closure.service.save()
        messages.success(request, f"AWS Services methods has been executed")


class ClosureAdmin(admin.ModelAdmin):
    inlines = [ConfigurationInline]
    list_display = ["id", "service", "execution_order"]


admin.site.register(AccessKey, AccessKeyAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(ValueType)
admin.site.register(Name)
admin.site.register(Method)
admin.site.register(DefaultConfiguration, DefaultConfigurationAdmin)
admin.site.register(ExecutionOrder, ExecutionOrderAdmin)
admin.site.register(Closure, ClosureAdmin)
admin.site.register(Response)
admin.site.register(PackageName)
admin.site.register(ConfigurationPackage)
admin.site.register(DefaultConfigurationPackage)
