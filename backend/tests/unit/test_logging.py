import logging
from typing import Any

from app.observability.logging import configure_logging


def test_configured_logging_adds_request_id_to_library_records(caplog: Any) -> None:
    configure_logging("INFO")

    with caplog.at_level(logging.INFO, logger="httpx"):
        logging.getLogger("httpx").info("library log")

    assert caplog.records
    assert caplog.records[-1].request_id == "-"
