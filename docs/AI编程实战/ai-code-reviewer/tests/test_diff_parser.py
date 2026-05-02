"""Tests for diff parser."""

from ai_code_reviewer.diff_parser import DiffParser


SAMPLE_DIFF = """diff --git a/src/main.py b/src/main.py
index abc123..def456 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,9 @@ def process_data(items):
     for item in items:
-        old_result = compute(item)
-        print(old_result)
+        new_result = compute_fast(item)
+        if new_result is not None:
+            print(new_result)
     return True
+
+def new_function():
+    return 42
"""


def test_parse_file_header():
    parser = DiffParser()
    files = parser.parse(SAMPLE_DIFF)

    assert len(files) == 1
    assert files[0].old_path == "src/main.py"
    assert files[0].new_path == "src/main.py"
    assert files[0].status == "modified"


def test_parse_hunk():
    parser = DiffParser()
    files = parser.parse(SAMPLE_DIFF)

    assert len(files[0].hunks) == 1
    hunk = files[0].hunks[0]
    assert hunk.old_start == 10
    assert hunk.new_start == 10


def test_parse_added_lines():
    parser = DiffParser()
    files = parser.parse(SAMPLE_DIFF)

    hunk = files[0].hunks[0]
    assert len(hunk.added_lines) == 4  # +++ 新行+空行


def test_parse_removed_lines():
    parser = DiffParser()
    files = parser.parse(SAMPLE_DIFF)

    hunk = files[0].hunks[0]
    assert len(hunk.removed_lines) == 2


def test_empty_diff():
    parser = DiffParser()
    files = parser.parse("")
    assert len(files) == 0


MULTI_FILE_DIFF = """diff --git a/a.py b/a.py
index a..b 100644
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-old
+new
diff --git a/b.py b/b.py
index c..d 100644
--- a/b.py
+++ b/b.py
@@ -1 +1 @@
-old2
+new2
"""


def test_multi_file():
    parser = DiffParser()
    files = parser.parse(MULTI_FILE_DIFF)
    assert len(files) == 2
    assert files[0].file_path == "a.py"
    assert files[1].file_path == "b.py"


def test_token_estimate():
    parser = DiffParser()
    files = parser.parse(SAMPLE_DIFF)
    assert files[0].estimate_tokens() > 0
    assert files[0].hunks[0].estimate_tokens() > 0
