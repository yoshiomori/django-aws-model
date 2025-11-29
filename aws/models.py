import re
import builtins
import importlib

from django.core.exceptions import ValidationError
from django.db import models


class AccessKey(models.Model):
    access_key_id = models.SlugField(max_length=20, unique=True, db_index=True)
    secret_access_key = models.SlugField(max_length=40)

    def __str__(self):
        return self.access_key_id


def validate_bucket_name(value: str):
    """
    Validate an S3 bucket name according to AWS rules.
    Raises ValidationError if invalid.
    """

    # Rule 1: Length between 3 and 63
    if not (3 <= len(value) <= 63):
        raise ValidationError("Bucket name must be between 3 and 63 characters long.")

    # Rule 2: Allowed characters (lowercase letters, numbers, periods, hyphens)
    if not re.fullmatch(r"[a-z0-9.-]+", value):
        raise ValidationError("Bucket name can only contain lowercase letters, numbers, periods (.), and hyphens (-).")

    # Rule 3: Must begin and end with a letter or number
    if not (value[0].isalnum() and value[-1].isalnum()):
        raise ValidationError("Bucket name must begin and end with a letter or number.")

    # Rule 4: Must not contain two adjacent periods
    if ".." in value:
        raise ValidationError("Bucket name must not contain two adjacent periods.")

    # Rule 5: Must not be formatted as an IP address
    ip_pattern = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
    if ip_pattern.match(value):
        raise ValidationError("Bucket name must not be formatted as an IP address.")

    # Rule 6: Must not start with restricted prefixes
    restricted_prefixes = ["xn--", "sthree-", "amzn-s3-demo-"]
    if any(value.startswith(prefix) for prefix in restricted_prefixes):
        raise ValidationError(f"Bucket name must not start with {restricted_prefixes}.")

    # Rule 7: Must not end with restricted suffixes
    restricted_suffixes = [
        "-s3alias",
        "--ol-s3",
        ".mrap",
        "--x-s3",
        "--table-s3"
    ]
    if any(value.endswith(suffix) for suffix in restricted_suffixes):
        raise ValidationError(f"Bucket name must not end with {restricted_suffixes}.")

    # Rule 8: Buckets used with Transfer Acceleration can't have periods
    if "." in value:
        raise ValidationError("Bucket names for Transfer Acceleration cannot contain periods (.).")

    # If all checks pass
    return value


class Name(models.Model):
    value = models.CharField(max_length=128, unique=True, db_index=True)

    def __str__(self):
        return self.value


class Method(models.Model):
    value = models.CharField(max_length=128, unique=True, db_index=True)

    def __str__(self):
        return self.value


class Service(models.Model):
    name = models.ForeignKey(Name, on_delete=models.PROTECT)
    method = models.ForeignKey(Method, on_delete=models.PROTECT)
    access_key = models.ForeignKey(AccessKey, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name}({self.method})"


class ValueType(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class DefaultConfiguration(models.Model):
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    value_type = models.ForeignKey(ValueType, on_delete=models.PROTECT)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)

    class Meta:
        unique_together = [["key", "service"]]


class Closure(models.Model):
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    execution_order = models.ForeignKey('ExecutionOrder', on_delete=models.PROTECT)
    variable_name = models.CharField(max_length=79, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        creating = self.pk is None
        response = super().save(*args, **kwargs)
        if creating:
            Configuration.objects.bulk_create(
                Configuration(
                    key=configuration.key,
                    value=configuration.value,
                    value_type=configuration.value_type,
                    closure=self
                )
                for configuration
                in self
                .service
                .defaultconfiguration_set
                .all()
            )
            configurationpackage_list = []
            for configuration in self.configuration_set.all():
                for default_configuration in configuration.closure.service.defaultconfiguration_set.filter(key=configuration.key):
                    for default_configuration_package in default_configuration.defaultconfigurationpackage_set.all():
                        configurationpackage_list.append(
                            ConfigurationPackage(
                                name=default_configuration_package.name,
                                configuration=configuration
                            )
                        )
            ConfigurationPackage.objects.bulk_create(configurationpackage_list)
        return response

    def __str__(self):
        return f'{self.service} {self.pk}'


class ExecutionOrder(models.Model):
    name = models.CharField(max_length=128, unique=True, db_index=True)
    service = models.ManyToManyField(Service, through=Closure)

    def __str__(self):
        return self.name


class Configuration(models.Model):
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    value_type = models.ForeignKey(ValueType, on_delete=models.PROTECT)
    closure = models.ForeignKey(Closure, on_delete=models.CASCADE)

    def get_value(self, env_var):
        if self.value_type.name == 'eval':
            qs = (
                self
                .configurationpackage_set
                .all()
                .values_list('name__value', flat=True)
            )
            local_env = {
                package: importlib.import_module(package)
                for package
                in qs
            }
            local_env.update(env_var)
            kwargs = {'locals': local_env}
        else:
            kwargs = {}
        return getattr(builtins, self.value_type.name)(self.value, **kwargs)

    class Meta:
        unique_together = [["key", "closure"]]


class Response(models.Model):
    value = models.JSONField()


class PackageName(models.Model):
    value = models.CharField(max_length=128, unique=True, db_index=True)

    def __str__(self):
        return self.value


class ConfigurationPackage(models.Model):
    name = models.ForeignKey(PackageName, on_delete=models.PROTECT)
    configuration = models.ForeignKey(Configuration, on_delete=models.PROTECT)
    
    class Meta:
        unique_together = [('name', 'configuration')]


class DefaultConfigurationPackage(models.Model):
    name = models.ForeignKey(PackageName, on_delete=models.PROTECT)
    configuration = models.ForeignKey(DefaultConfiguration, on_delete=models.PROTECT)

    class Meta:
        unique_together = [('name', 'configuration')]
