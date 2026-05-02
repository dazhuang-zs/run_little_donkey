"""Git diff parsing utilities."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiffHunk:
    """一个diff块（hunk）"""
    old_start: int          # 原文件起始行
    old_count: int          # 原文件行数
    new_start: int          # 新文件起始行
    new_count: int          # 新文件行数
    header: str             # @@ ... @@ 头
    lines: list[str]        # diff行内容
    added_lines: list[tuple[int, str]] = field(default_factory=list)   # 新增行 [(行号, 内容)]
    removed_lines: list[tuple[int, str]] = field(default_factory=list) # 删除行 [(行号, 内容)]

    def estimate_tokens(self) -> int:
        """粗略估计此hunk消耗的token数（~4 chars/token）"""
        text = "\n".join(self.lines)
        return len(text) // 3 + 1


@dataclass
class FileDiff:
    """单个文件的diff"""
    old_path: str
    new_path: str
    status: str             # modified / added / deleted / renamed
    hunks: list[DiffHunk] = field(default_factory=list)

    @property
    def file_path(self) -> str:
        """显示用的文件路径"""
        return self.new_path if self.new_path != "/dev/null" else self.old_path

    def estimate_tokens(self) -> int:
        return sum(h.estimate_tokens() for h in self.hunks)


class DiffParser:
    """解析git diff输出为结构化数据"""

    # 匹配diff文件头: diff --git a/file b/file
    FILE_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$")
    # 匹配文件状态: new file / deleted / renamed / index
    NEW_FILE_RE = re.compile(r"^new file mode")
    DELETED_FILE_RE = re.compile(r"^deleted file mode")
    RENAME_RE = re.compile(r"^rename from")
    # 匹配hunk头: @@ -old,count +new,count @@
    HUNK_HEADER_RE = re.compile(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")

    def parse(self, diff_text: str) -> list[FileDiff]:
        """解析完整的diff文本"""
        files: list[FileDiff] = []
        current_file: Optional[FileDiff] = None
        current_hunk: Optional[DiffHunk] = None
        in_hunk = False

        for line in diff_text.split("\n"):
            # 检查文件头
            file_match = self.FILE_HEADER_RE.match(line)
            if file_match:
                # 保存上一个文件的hunk
                if current_hunk and current_file:
                    current_file.hunks.append(current_hunk)
                if current_file:
                    files.append(current_file)

                current_file = FileDiff(
                    old_path=file_match.group(1),
                    new_path=file_match.group(2),
                    status="modified",
                )
                current_hunk = None
                in_hunk = False
                continue

            if current_file is None:
                continue

            # 检查文件状态
            if self.NEW_FILE_RE.match(line):
                current_file.status = "added"
                continue
            if self.DELETED_FILE_RE.match(line):
                current_file.status = "deleted"
                continue
            if self.RENAME_RE.match(line):
                current_file.status = "renamed"
                continue

            # 检查hunk头
            hunk_match = self.HUNK_HEADER_RE.match(line)
            if hunk_match:
                if current_hunk and current_file:
                    current_file.hunks.append(current_hunk)

                old_start = int(hunk_match.group(1))
                old_count_str = hunk_match.group(2)
                new_start = int(hunk_match.group(3))
                new_count_str = hunk_match.group(4)

                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=int(old_count_str) if old_count_str else 1,
                    new_start=new_start,
                    new_count=int(new_count_str) if new_count_str else 1,
                    header=line,
                    lines=[],
                )
                in_hunk = True
                current_hunk.lines.append(line)
                continue

            # hunk内容行
            if in_hunk and current_hunk:
                current_hunk.lines.append(line)
                line_num = self._get_line_number(line, current_hunk)
                if line.startswith("+"):
                    current_hunk.added_lines.append((line_num, line[1:]))
                elif line.startswith("-"):
                    current_hunk.removed_lines.append((line_num, line[1:]))

        # 保存最后一个
        if current_hunk and current_file:
            current_file.hunks.append(current_hunk)
        if current_file:
            files.append(current_file)

        return files

    def _get_line_number(self, line: str, hunk: DiffHunk) -> int:
        """根据diff行计算在新文件中的行号"""
        if line.startswith("+"):
            # 新增行：相对于new_start偏移
            added_before = sum(
                1 for l in hunk.lines[:hunk.lines.index(line)]
                if l.startswith("+") or l.startswith(" ")
            )
            return hunk.new_start + added_before
        elif line.startswith("-"):
            removed_before = sum(
                1 for l in hunk.lines[:hunk.lines.index(line)]
                if l.startswith("-") or l.startswith(" ")
            )
            return hunk.old_start + removed_before
        return 0

    @staticmethod
    def get_git_diff(target: str = "HEAD", staged: bool = False) -> str:
        """获取git diff输出"""
        from git import Repo
        from git.exc import InvalidGitRepositoryError

        try:
            repo = Repo(".")
        except InvalidGitRepositoryError:
            raise RuntimeError("当前目录不是git仓库")

        if staged:
            diff_text = repo.git.diff("--cached")
        elif target == "HEAD":
            diff_text = repo.git.diff("HEAD~1", "HEAD")
        else:
            diff_text = repo.git.diff(target)

        return diff_text or ""
