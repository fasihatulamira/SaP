from database import _clamp_pagination, _paginated_result


def test_clamp_pagination_defaults():
    page, limit = _clamp_pagination("bad", "bad")
    assert page == 1
    assert limit == 10


def test_clamp_pagination_caps_limit():
    page, limit = _clamp_pagination(2, 500)
    assert page == 2
    assert limit == 100


def test_paginated_result_empty():
    result = _paginated_result([], 0, 1, 8)
    assert result["total"] == 0
    assert result["total_pages"] == 1
    assert result["items"] == []
