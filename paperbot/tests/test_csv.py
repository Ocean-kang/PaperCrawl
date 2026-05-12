import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from paperbot.models.paper import Paper
from paperbot.exporters.csv_exporter import export_csv


def test_csv_export():
    papers = [
        Paper(
            title="Test Paper One",
            authors=["Alice", "Bob"],
            abstract="This is a test abstract.",
            pdf_url="https://example.com/paper1.pdf",
            detail_url="https://example.com/paper1",
            conference="CVPR",
            year=2025,
            source="cvf",
            keywords=["deep learning", "vision"],
        ),
        Paper(
            title="Test Paper Two",
            authors=["Charlie"],
            abstract=None,
            pdf_url=None,
            detail_url="https://example.com/paper2",
            conference="CVPR",
            year=2025,
            source="cvf",
        ),
    ]

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = export_csv(papers, filepath=f.name)

    assert path.exists(), f"CSV file not found: {path}"
    content = path.read_text(encoding="utf-8")
    assert "Test Paper One" in content
    assert "Test Paper Two" in content
    assert "Alice; Bob" in content
    print(f"CSV export OK: {path}")
    print(content)

    path.unlink()


if __name__ == "__main__":
    test_csv_export()
