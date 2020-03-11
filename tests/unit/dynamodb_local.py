import json
import pathlib
from decimal import Decimal

from boto3.resources.base import ServiceResource


class DynamoDBLocal(object):
    def __init__(self, table_name: str, dynamodb_resource: ServiceResource):
        self.table_name = table_name
        self.dynamodb_resource = dynamodb_resource
        self.create()
        self.table = dynamodb_resource.Table(table_name)

    def abs_path(self, relation_path: str) -> str:
        return str(pathlib.Path(__file__).parent.joinpath(relation_path).resolve())

    def create(self):
        relation_path = f"fixtures/tables/{self.table_name}/definition.json"
        definition = json.load(open(self.abs_path(relation_path)))
        return self.dynamodb_resource.create_table(**definition)

    def set_data(self, data_name: str):
        relation_path = f"fixtures/tables/{self.table_name}/{data_name}.json"
        data = json.load(open(self.abs_path(relation_path)))
        with self.table.batch_writer() as batch:
            for item in data:
                batch.put_item(self.convert(item))

    def convert(self, raw: any):
        if isinstance(raw, dict):
            return {k: self.convert(v) for k, v in raw.items()}
        elif isinstance(raw, list):
            return [self.convert(x) for x in raw]
        elif isinstance(raw, float):
            return Decimal(str(raw))
        else:
            return raw
