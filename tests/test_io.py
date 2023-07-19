from io import StringIO

import pandas as pd
import pytest
from moto import mock_s3

from runpandarun import io
from tests.util import setup_s3_bucket


def test_io_read(fixtures_path):
    df = io.read_pandas(fixtures_path / "testdata.csv")
    assert len(df) == 10000
    assert list(df.columns) == ["state", "city", "amount", "date"]

    df = io.read_pandas(fixtures_path / "testdata.json", handler="read_json")
    assert len(df) == 10000
    assert list(df.columns) == ["state", "integer", "date"]
    assert not isinstance(df["integer"][0], str)
    df = io.read_pandas(
        fixtures_path / "testdata.json",
        handler="read_json",
        **{"dtype": {"integer": str}},
    )
    assert isinstance(df["integer"][0], str)

    df = io.read_pandas(
        fixtures_path / "lobbyregister.json",
        handler="json_normalize",
        record_path="results",
    )
    assert len(df) == 17
    assert "registerNumber" in df.columns


def test_io_write(fixtures_path, tmp_path):
    df = io.read_pandas(fixtures_path / "testdata.csv")
    io.write_pandas(df, tmp_path / "testdata.csv")
    df_out = pd.read_csv(tmp_path / "testdata.csv")
    assert len(df) == len(df_out)
    out = StringIO()
    assert not out.closed
    io.write_pandas(df.head(), out)
    assert out.closed


def test_io_read_remote(server):
    df = io.read_pandas(server % "testdata.csv")
    assert len(df) == 10000
    assert list(df.columns) == ["state", "city", "amount", "date"]

    df = io.read_pandas(
        server % "lobbyregister.json",
        handler="json_normalize",
        record_path="results",
    )
    assert len(df) == 17
    assert "registerNumber" in df.columns


@mock_s3
def test_io_s3():
    setup_s3_bucket(with_content=True)
    # https://stackoverflow.com/questions/74897486/how-to-resolve-pandas-read-csv-not-working-for-mock-s3
    # df = io.read_pandas("s3://runpandarun/testdata.csv")
    # assert len(df) == 10000
    # assert list(df.columns) == ["state", "city", "amount", "date"]

    # io.write_pandas(df.head(), "s3://runpandarun/testdata2.csv")
    # df = io.read_pandas("s3://runpandarun/testdata2.csv")
    # assert len(df) == 5
    # assert list(df.columns) == ["state", "city", "amount", "date"]


def test_io_guess_handler():
    handlers = {
        "xls": "excel",
        "xlsx": "excel",
        "csv": "csv",
        "html": "html",
        "json": "json",
        "xml": "xml",
    }
    for ext, h in handlers.items():
        assert io.guess_handler(f"/foo/bar/data.{ext}") == h

    with pytest.raises(NotImplementedError):
        io.guess_handler("")

    with pytest.raises(NotImplementedError):
        io.guess_handler("data.sql")
