import boto3
import pytest
from boto3.resources.base import ServiceResource

from .dynamodb_local import DynamoDBLocal


@pytest.fixture(scope="function")
def set_env(request, monkeypatch):
    for k, v in request.param.items():
        monkeypatch.setenv(k, v)


@pytest.fixture(scope="session")
def dynamodb_resource() -> ServiceResource:
    return boto3.resource("dynamodb", endpoint_url="http://localhost:4569")


@pytest.fixture(scope="function")
def dynamodb(dynamodb_resource: ServiceResource, request) -> ServiceResource:
    table_store = []
    for info in request.param:
        table_name = info[0]
        local = DynamoDBLocal(table_name, dynamodb_resource)
        table_store.append(local)

        if len(info) > 1:
            local.set_data(info[1])

    yield dynamodb_resource

    for local in table_store:
        local.table.delete()
