import re
from typing import Dict, List, Optional, Tuple


class DiffHunk:
    def __init__(self, old_start: int, old_len: int, new_start: int, new_len: int, lines: List[str]):
        self.old_start = old_start
        self.old_len = old_len
        self.new_start = new_start
        self.new_len = new_len
        self.lines = lines  # lines including +, -, space


class ParsedFileDiff:
    def __init__(self, file_path: str, old_path: Optional[str] = None, status: str = "modified"):
        self.file_path = file_path
        self.old_path = old_path
        self.status = status  # modified, added, deleted, renamed
        self.hunks: List[DiffHunk] = []
        self.added_lines: List[Tuple[int, str]] = []  # (new_line_num, line_content)
        self.deleted_lines: List[Tuple[int, str]] = []  # (old_line_num, line_content)
        self.context_lines: List[Tuple[int, str]] = []  # (new_line_num, line_content)
        self.all_lines: List[str] = []


HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_unified_diff(diff_text: str) -> Dict[str, ParsedFileDiff]:
    """
    Parses a unified diff string into a mapping of file_path -> ParsedFileDiff.
    Categorizes lines into added (+), deleted (-), and context ( ).
    Tracks file lifecycle status (modified, added, deleted, renamed).
    """
    files: Dict[str, ParsedFileDiff] = {}
    current_file: Optional[ParsedFileDiff] = None
    current_hunk: Optional[DiffHunk] = None
    new_line_ptr = 0
    old_line_ptr = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" ")
            if len(parts) >= 4:
                old_p = parts[2][2:] if parts[2].startswith("a/") else parts[2]
                new_p = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                status = "renamed" if old_p != new_p and old_p != "/dev/null" and new_p != "/dev/null" else "modified"
                current_file = ParsedFileDiff(
                    file_path=new_p,
                    old_path=old_p if status == "renamed" else None,
                    status=status
                )
                files[new_p] = current_file
                current_hunk = None
            continue

        if current_file is None:
            continue

        if line.startswith("new file mode "):
            current_file.status = "added"
            continue
        if line.startswith("deleted file mode "):
            current_file.status = "deleted"
            continue
        if line.startswith("rename from "):
            current_file.status = "renamed"
            current_file.old_path = line.replace("rename from ", "").strip()
            continue
        if line.startswith("rename to "):
            current_file.status = "renamed"
            continue
        if line.startswith("--- /dev/null"):
            current_file.status = "added"
            continue
        if line.startswith("+++ /dev/null"):
            current_file.status = "deleted"
            continue

        match = HUNK_HEADER_REGEX.match(line)
        if match:
            old_start = int(match.group(1))
            old_len = int(match.group(2)) if match.group(2) else 1
            new_start = int(match.group(3))
            new_len = int(match.group(4)) if match.group(4) else 1

            current_hunk = DiffHunk(old_start, old_len, new_start, new_len, [])
            current_file.hunks.append(current_hunk)
            new_line_ptr = new_start
            old_line_ptr = old_start
            continue

        if current_hunk is not None:
            current_hunk.lines.append(line)
            current_file.all_lines.append(line)

            if line.startswith("+"):
                content = line[1:]
                current_file.added_lines.append((new_line_ptr, content))
                new_line_ptr += 1
            elif line.startswith("-"):
                content = line[1:]
                current_file.deleted_lines.append((old_line_ptr, content))
                old_line_ptr += 1
            elif line.startswith(" "):
                content = line[1:]
                current_file.context_lines.append((new_line_ptr, content))
                new_line_ptr += 1
                old_line_ptr += 1

    return files


def verify_evidence_in_diff(
    file_path: str,
    snippet: str,
    line_start: Optional[int],
    line_end: Optional[int],
    parsed_files: Dict[str, ParsedFileDiff],
) -> Tuple[bool, bool, Optional[str]]:
    """
    Grounding verification: checks if the cited file and code snippet exist in the diff.
    Distinguishes modified lines (+/-) from surrounding context lines ( ).
    Returns: (is_verified, is_changed_line, verified_snippet)
    """
    if file_path not in parsed_files:
        matching_paths = [p for p in parsed_files.keys() if p.lower() == file_path.lower() or p.endswith(file_path)]
        if not matching_paths:
            return False, False, None
        file_path = matching_paths[0]

    parsed = parsed_files[file_path]
    clean_snippet = snippet.strip()
    if not clean_snippet:
        return False, False, None

    # 1. Check if snippet matches within modified lines (+ / -)
    added_text = "\n".join(c for _, c in parsed.added_lines)
    deleted_text = "\n".join(c for _, c in parsed.deleted_lines)

    if clean_snippet in added_text or clean_snippet in deleted_text:
        return True, True, clean_snippet

    for _, c in parsed.added_lines + parsed.deleted_lines:
        c_strip = c.strip()
        if c_strip and (clean_snippet in c_strip or c_strip in clean_snippet):
            return True, True, clean_snippet

    # 2. Check if snippet matches within surrounding context lines ( )
    context_text = "\n".join(c for _, c in parsed.context_lines)
    if clean_snippet in context_text:
        return True, False, clean_snippet

    for _, c in parsed.context_lines:
        c_strip = c.strip()
        if c_strip and (clean_snippet in c_strip or c_strip in clean_snippet):
            return True, False, clean_snippet

    # 3. Check across raw unstripped diff lines
    for raw_line in parsed.all_lines:
        content = raw_line[1:].strip() if len(raw_line) > 1 else ""
        if content and (clean_snippet in content or content in clean_snippet):
            is_changed = raw_line.startswith("+") or raw_line.startswith("-")
            return True, is_changed, clean_snippet

    return False, False, None
