import re
from typing import Dict, List, Optional, Set, Tuple


class DiffHunk:
    def __init__(self, old_start: int, old_len: int, new_start: int, new_len: int, lines: List[str]):
        self.old_start = old_start
        self.old_len = old_len
        self.new_start = new_start
        self.new_len = new_len
        self.lines = lines  # lines including +, -, space


class ParsedFileDiff:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.hunks: List[DiffHunk] = []
        self.added_lines: List[Tuple[int, str]] = []  # (new_line_num, line_content)
        self.deleted_lines: List[Tuple[int, str]] = []  # (old_line_num, line_content)
        self.all_lines: List[str] = []


HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_unified_diff(diff_text: str) -> Dict[str, ParsedFileDiff]:
    """
    Parses a unified diff string into a mapping of file_path -> ParsedFileDiff.
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
                path = parts[3]
                if path.startswith("b/"):
                    path = path[2:]
                current_file = ParsedFileDiff(file_path=path)
                files[path] = current_file
                current_hunk = None
            continue

        if current_file is None:
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
                new_line_ptr += 1
                old_line_ptr += 1

    return files


def verify_evidence_in_diff(
    file_path: str,
    snippet: str,
    line_start: Optional[int],
    line_end: Optional[int],
    parsed_files: Dict[str, ParsedFileDiff],
) -> Tuple[bool, Optional[str]]:
    """
    Grounding verification: checks if the cited file and code snippet actually exist in the retrieved diff.
    Returns: (is_verified, verified_snippet_or_normalized)
    """
    if file_path not in parsed_files:
        # Check case-insensitive or basename fallback
        matching_paths = [p for p in parsed_files.keys() if p.lower() == file_path.lower() or p.endswith(file_path)]
        if not matching_paths:
            return False, None
        file_path = matching_paths[0]

    parsed = parsed_files[file_path]
    clean_snippet = snippet.strip()
    if not clean_snippet:
        return False, None

    # Check against raw diff lines
    for raw_line in parsed.all_lines:
        content = raw_line[1:].strip() if len(raw_line) > 1 else ""
        if clean_snippet in content or content in clean_snippet:
            return True, clean_snippet

    # Check multiline matches across added/deleted lines
    added_text = "\n".join(c for _, c in parsed.added_lines)
    deleted_text = "\n".join(c for _, c in parsed.deleted_lines)

    if clean_snippet in added_text or clean_snippet in deleted_text:
        return True, clean_snippet

    return False, None
