import pytest

import index


class TestUpdateSackCounter(object):
    @pytest.mark.parametrize(
        "dynamodb, table_name, amount, expected",
        [
            ([["DataStoreTable"]], "DataStoreTable", 1, 1),
            ([["DataStoreTable"]], "DataStoreTable", 2, 2),
            ([["DataStoreTable", "sack_counter_data"]], "DataStoreTable", 1, 33),
            ([["DataStoreTable", "sack_counter_data"]], "DataStoreTable", 2, 34),
        ],
        indirect=["dynamodb"],
    )
    def test_normal(self, dynamodb, table_name, amount, expected):
        actual = index.update_sack_counter(amount, table_name, dynamodb)
        assert actual == expected
