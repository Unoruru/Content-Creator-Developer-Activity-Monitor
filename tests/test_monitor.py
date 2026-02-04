"""Tests for the monitor module."""

import tempfile
from pathlib import Path

import pytest

from src.monitor import (
    compute_hash,
    extract_content,
    load_previous_hash,
    save_hash,
)


class TestComputeHash:
    """Tests for compute_hash function."""

    def test_consistency(self):
        """Same input should produce same hash."""
        content = "Hello, World!"
        hash1 = compute_hash(content)
        hash2 = compute_hash(content)
        assert hash1 == hash2

    def test_different_input(self):
        """Different input should produce different hash."""
        hash1 = compute_hash("Hello, World!")
        hash2 = compute_hash("Hello, World?")
        assert hash1 != hash2

    def test_empty_string(self):
        """Empty string should produce valid hash."""
        result = compute_hash("")
        assert len(result) == 64  # SHA256 produces 64 hex characters

    def test_unicode(self):
        """Unicode content should be handled correctly."""
        result = compute_hash("你好世界 🌍")
        assert len(result) == 64


class TestExtractContent:
    """Tests for extract_content function."""

    def test_full_page_extraction(self):
        """Should extract text from full page when no selector."""
        html = "<html><body><p>Hello</p><p>World</p></body></html>"
        result = extract_content(html, None)
        assert "Hello" in result
        assert "World" in result

    def test_with_selector(self):
        """Should extract only selected element."""
        html = """
        <html>
            <body>
                <div id="header">Header</div>
                <div id="content">Main Content</div>
                <div id="footer">Footer</div>
            </body>
        </html>
        """
        result = extract_content(html, "#content")
        assert result == "Main Content"

    def test_strips_scripts(self):
        """Should remove script tags."""
        html = "<html><body><script>alert('evil')</script><p>Content</p></body></html>"
        result = extract_content(html, None)
        assert "alert" not in result
        assert "Content" in result

    def test_strips_styles(self):
        """Should remove style tags."""
        html = "<html><body><style>.foo{color:red}</style><p>Content</p></body></html>"
        result = extract_content(html, None)
        assert "color" not in result
        assert "Content" in result

    def test_normalizes_whitespace(self):
        """Should normalize multiple whitespace to single space."""
        html = "<html><body><p>Hello    World\n\n\tTest</p></body></html>"
        result = extract_content(html, None)
        assert "  " not in result
        assert "\n" not in result
        assert "\t" not in result

    def test_invalid_selector_raises_error(self):
        """Should raise error for non-matching selector."""
        from src.monitor import MonitorError

        html = "<html><body><p>Content</p></body></html>"
        with pytest.raises(MonitorError, match="did not match"):
            extract_content(html, "#nonexistent")


class TestHashFileOperations:
    """Tests for load_previous_hash and save_hash functions."""

    def test_load_existing_file(self, tmp_path):
        """Should read hash from existing file."""
        hash_file = tmp_path / "hash.txt"
        expected_hash = "abc123def456"
        hash_file.write_text(expected_hash)

        result = load_previous_hash(str(hash_file))
        assert result == expected_hash

    def test_load_missing_file(self, tmp_path):
        """Should return None for missing file."""
        result = load_previous_hash(str(tmp_path / "nonexistent.txt"))
        assert result is None

    def test_load_strips_whitespace(self, tmp_path):
        """Should strip whitespace from loaded hash."""
        hash_file = tmp_path / "hash.txt"
        hash_file.write_text("  abc123  \n")

        result = load_previous_hash(str(hash_file))
        assert result == "abc123"

    def test_save_creates_file(self, tmp_path):
        """Should create file with hash."""
        hash_file = tmp_path / "hash.txt"
        save_hash(str(hash_file), "abc123")

        assert hash_file.exists()
        assert hash_file.read_text() == "abc123"

    def test_save_creates_directories(self, tmp_path):
        """Should create parent directories if needed."""
        hash_file = tmp_path / "subdir" / "nested" / "hash.txt"
        save_hash(str(hash_file), "abc123")

        assert hash_file.exists()

    def test_save_overwrites_existing(self, tmp_path):
        """Should overwrite existing file."""
        hash_file = tmp_path / "hash.txt"
        hash_file.write_text("old_hash")

        save_hash(str(hash_file), "new_hash")
        assert hash_file.read_text() == "new_hash"
