from dalit_archive_scrapers.utils import clean_text, extract_query_terms, slugify


def test_slugify_basic() -> None:
    assert slugify("Dalit Entrepreneurship in Public Policy") == "dalit-entrepreneurship-in-public-policy"


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  A \n  B\tC ") == "A B C"


def test_extract_query_terms() -> None:
    assert extract_query_terms("https://example.com/search?q=Dalits&page=1", ("q",)) == ["dalits"]
