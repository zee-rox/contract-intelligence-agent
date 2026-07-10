import logging

from app.observability.context import get_request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
    )
    root = logging.getLogger()
    if not any(isinstance(filter_item, RequestIdFilter) for filter_item in root.filters):
        root.addFilter(RequestIdFilter())
