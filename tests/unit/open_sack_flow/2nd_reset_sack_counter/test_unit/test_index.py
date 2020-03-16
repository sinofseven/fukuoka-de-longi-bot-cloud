import pytest

import index


class TestResetSackCounter(object):
    @pytest.mark.parametrize(
        "dynamodb, table_name, expected",
        [([["DataStoreTable", "sack_counter_data"]], "DataStoreTable", 0)],
        indirect=["dynamodb"],
    )
    def test_normal(self, dynamodb, table_name, expected):
        index.reset_sack_counter(table_name, dynamodb)

        resp = dynamodb.Table(table_name).get_item(Key={"partitionId": "sackCounter", "sortId": "counter"})
        assert resp["Item"]["times"] == expected
