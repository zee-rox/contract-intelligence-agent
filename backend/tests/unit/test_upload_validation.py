import pytest

from app.config import Settings
from app.ingestion.service import IngestionError, register_document, sanitize_filename


def test_register_document_rejects_invalid_signature(tmp_path) -> None:
    settings = Settings(storage_root=tmp_path)
    with pytest.raises(IngestionError) as exc:
        register_document("contract.pdf", "application/pdf", b"not a pdf", settings)
    assert exc.value.code == "unsupported_file_type"


def test_sanitize_filename_blocks_path_traversal() -> None:
    assert sanitize_filename("../../secret contract.pdf") == "secret_contract.pdf"


def test_register_document_accepts_pdf_signature(tmp_path) -> None:
    settings = Settings(storage_root=tmp_path)
    record = register_document("contract.pdf", "application/pdf", b"%PDF-1.7\n", settings)
    assert record.source_type == "pdf"
    assert record.status == "registered"
