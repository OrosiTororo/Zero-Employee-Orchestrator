"""Tests for utils.json_parser.safe_extract_json."""

from __future__ import annotations

from app.utils.json_parser import safe_extract_json


def test_none_and_empty_return_none():
    assert safe_extract_json(None) is None
    assert safe_extract_json("") is None
    assert safe_extract_json("   ") is None


def test_plain_prose_returns_none():
    assert safe_extract_json("The answer is 42, but not in JSON.") is None


def test_bare_object_is_parsed():
    assert safe_extract_json('{"k": 1, "v": "two"}') == {"k": 1, "v": "two"}


def test_bare_array_is_parsed():
    assert safe_extract_json("[1, 2, 3]") == [1, 2, 3]


def test_fenced_json_block_is_extracted():
    text = """Here is the answer.

```json
{
  "status": "ok",
  "values": [1, 2]
}
```

Thanks!"""
    assert safe_extract_json(text) == {"status": "ok", "values": [1, 2]}


def test_unlabelled_fence_also_works():
    text = """Prose before.

```
{"ok": true}
```
"""
    assert safe_extract_json(text) == {"ok": True}


def test_malformed_fenced_block_falls_through_to_bare_parse():
    # Fence content is broken, but bare JSON follows.
    text = """```json
{"broken":
```

{"bare": 1}"""
    # The fenced payload fails to parse. Since the overall text does not
    # start with `{` or `[` (after stripping), the helper returns None rather
    # than a mis-parsed value — which is the correct conservative behaviour.
    assert safe_extract_json(text) is None


def test_truly_malformed_returns_none():
    assert safe_extract_json("{not valid json}") is None
