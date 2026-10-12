import re
from typing import Dict, List, Optional, Set, Tuple

from app.diff_parser import ParsedFileDiff
from app.schemas import (
    ChangeImpactSummary,
    DiffSummary,
    FileImpact,
    InterfaceChange,
    RiskFinding,
)

# Regex patterns for directly visible interface changes in code diffs
PY_FUNC_REGEX = re.compile(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\((.*?)\)")
PY_CLASS_REGEX = re.compile(r"^\s*class\s+([a-zA-Z0-9_]+)(?:\((.*?)\))?:")
PY_ROUTE_REGEX = re.compile(
    r"^\s*@(?:app|router|blueprint|bp|api)\.(get|post|put|delete|patch|route)\s*\((.*?)\)"
)

JS_EXPORT_FUNC_REGEX = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\((.*?)\)"
)
JS_EXPORT_CONST_REGEX = re.compile(
    r"^\s*export\s+const\s+([a-zA-Z0-9_]+)\s*="
)
JS_EXPORT_TYPE_REGEX = re.compile(
    r"^\s*export\s+(?:type|interface)\s+([a-zA-Z0-9_]+)"
)
JS_ROUTE_REGEX = re.compile(
    r"^\s*(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
)

CONFIG_ASSIGN_REGEX = re.compile(r"^\s*([A-Z][A-Z0-9_]{2,})\s*[:=]\s*(.+)")


def classify_file_path(file_path: str) -> str:
    """
    Classifies a file path into standard categories based on path structure and file naming:
    - Documentation
    - Tests
    - Authentication
    - Database / Schema
    - API / Contracts
    - Configuration
    - Application Logic
    - Other
    """
    path_lower = file_path.lower()
    file_name = path_lower.split("/")[-1]

    # 1. Documentation
    if (
        path_lower.startswith("docs/")
        or "/docs/" in path_lower
        or "/doc/" in path_lower
        or file_name.endswith((".md", ".rst", ".txt", ".adoc"))
        or file_name in ("license", "changelog", "notice", "contributing.md", "authors")
    ):
        return "Documentation"

    # 2. Tests
    if (
        path_lower.startswith("tests/")
        or "/tests/" in path_lower
        or path_lower.startswith("test/")
        or "/test/" in path_lower
        or "/__tests__/" in path_lower
        or "/spec/" in path_lower
        or file_name.startswith("test_")
        or file_name.endswith(
            (
                "_test.py",
                "_spec.rb",
                ".test.js",
                ".test.ts",
                ".test.jsx",
                ".test.tsx",
                ".spec.js",
                ".spec.ts",
                ".spec.jsx",
                ".spec.tsx",
            )
        )
    ):
        return "Tests"

    # 3. Authentication
    auth_indicators = (
        "auth",
        "login",
        "oauth",
        "jwt",
        "session",
        "credential",
        "permission",
        "rbac",
        "password",
    )
    if any(k in path_lower for k in auth_indicators):
        return "Authentication"

    # 4. Database / Schema
    db_indicators = (
        "migration",
        "schema",
        "models",
        "alembic",
        "prisma",
        "entities",
        "repository",
        "sql",
        "db/",
    )
    if any(k in path_lower for k in db_indicators) or file_name.endswith(".sql"):
        return "Database / Schema"

    # 5. API / Contracts
    api_indicators = (
        "api",
        "route",
        "controller",
        "endpoint",
        "openapi",
        "swagger",
        "graphql",
        "proto",
        "urls.py",
        "contract",
    )
    if any(k in path_lower for k in api_indicators) or file_name.endswith((".proto", ".graphql")):
        return "API / Contracts"

    # 6. Configuration
    config_indicators = (
        "config",
        "settings",
        "docker",
        ".env",
        "ci/",
        "workflows",
        "package.json",
        "requirements",
        "pyproject.toml",
        "cargo.toml",
        "gemfile",
    )
    if any(k in path_lower for k in config_indicators) or file_name.endswith(
        (".yaml", ".yml", ".toml", ".ini", ".cfg", ".json", ".conf")
    ):
        return "Configuration"

    # 7. Application Logic
    code_extensions = (
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".rb",
        ".php",
        ".cs",
        ".swift",
        ".kt",
    )
    if file_name.endswith(code_extensions):
        return "Application Logic"

    return "Other"


def detect_interface_changes(parsed: ParsedFileDiff) -> List[InterfaceChange]:
    """
    Identifies directly visible changes to functions, routes, classes, and exported interfaces
    only when supported by the actual diff lines (+ and -).
    """
    interfaces: List[InterfaceChange] = []
    seen_keys: Set[Tuple[str, str]] = set()

    added_funcs: Dict[str, Tuple[int, str]] = {}
    deleted_funcs: Dict[str, Tuple[int, str]] = {}

    # Scan added lines
    for line_num, content in parsed.added_lines:
        # Python function
        m = PY_FUNC_REGEX.match(content)
        if m:
            func_name = m.group(1)
            params = m.group(2).strip()
            added_funcs[func_name] = (line_num, params)

        # Python class
        m_cls = PY_CLASS_REGEX.match(content)
        if m_cls:
            cls_name = m_cls.group(1)
            key = ("added_class", cls_name)
            if key not in seen_keys:
                seen_keys.add(key)
                interfaces.append(
                    InterfaceChange(
                        change_type="added_class",
                        name=cls_name,
                        details=f"Class defined: class {cls_name}",
                        line_number=line_num,
                    )
                )

        # Python route decorator
        m_rt = PY_ROUTE_REGEX.match(content)
        if m_rt:
            method = m_rt.group(1).upper()
            route_path = m_rt.group(2).strip().strip("'\"")
            key = ("added_route", f"{method} {route_path}")
            if key not in seen_keys:
                seen_keys.add(key)
                interfaces.append(
                    InterfaceChange(
                        change_type="added_route",
                        name=f"{method} {route_path}",
                        details=f"Endpoint route defined: {m_rt.group(0).strip()}",
                        line_number=line_num,
                    )
                )

        # JS/TS export function
        m_js_f = JS_EXPORT_FUNC_REGEX.match(content)
        if m_js_f:
            fn_name = m_js_f.group(1)
            key = ("added_function", fn_name)
            if key not in seen_keys:
                seen_keys.add(key)
                interfaces.append(
                    InterfaceChange(
                        change_type="added_function",
                        name=fn_name,
                        details=f"Exported function: {fn_name}({m_js_f.group(2).strip()})",
                        line_number=line_num,
                    )
                )

        # JS/TS export const
        m_js_c = JS_EXPORT_CONST_REGEX.match(content)
        if m_js_c:
            const_name = m_js_c.group(1)
            key = ("added_export", const_name)
            if key not in seen_keys:
                seen_keys.add(key)
                interfaces.append(
                    InterfaceChange(
                        change_type="added_export",
                        name=const_name,
                        details=f"Exported symbol: {const_name}",
                        line_number=line_num,
                    )
                )

        # JS/TS export type/interface
        m_js_t = JS_EXPORT_TYPE_REGEX.match(content)
        if m_js_t:
            type_name = m_js_t.group(1)
            key = ("added_type", type_name)
            if key not in seen_keys:
                seen_keys.add(key)
                interfaces.append(
                    InterfaceChange(
                        change_type="added_type",
                        name=type_name,
                        details=f"Exported type/interface: {type_name}",
                        line_number=line_num,
                    )
                )

        # Config assignment
        m_cfg = CONFIG_ASSIGN_REGEX.match(content)
        if m_cfg and not content.strip().startswith("#"):
            var_name = m_cfg.group(1)
            key = ("modified_config", var_name)
            if key not in seen_keys:
                seen_keys.add(key)
                interfaces.append(
                    InterfaceChange(
                        change_type="modified_config",
                        name=var_name,
                        details=f"Config variable set: {var_name}",
                        line_number=line_num,
                    )
                )

    # Scan deleted lines
    for line_num, content in parsed.deleted_lines:
        m = PY_FUNC_REGEX.match(content)
        if m:
            func_name = m.group(1)
            params = m.group(2).strip()
            deleted_funcs[func_name] = (line_num, params)

    # Correlate added vs deleted functions (modified vs added vs removed)
    for fn, (line_num, params) in added_funcs.items():
        if fn in deleted_funcs:
            old_line, old_params = deleted_funcs[fn]
            param_note = (
                f"Signature modified: ({old_params}) -> ({params})"
                if old_params != params
                else f"Function body modified: {fn}"
            )
            interfaces.append(
                InterfaceChange(
                    change_type="modified_function",
                    name=fn,
                    details=param_note,
                    line_number=line_num,
                )
            )
        else:
            interfaces.append(
                InterfaceChange(
                    change_type="added_function",
                    name=fn,
                    details=f"Function introduced: {fn}({params})",
                    line_number=line_num,
                )
            )

    for fn, (old_line, old_params) in deleted_funcs.items():
        if fn not in added_funcs:
            interfaces.append(
                InterfaceChange(
                    change_type="removed_function",
                    name=fn,
                    details=f"Function removed: {fn}({old_params})",
                    line_number=old_line,
                )
            )

    # Keep strictly bounded to top 10 interface changes per file to prevent unbounded bloat
    return interfaces[:10]


def infer_potential_impacts(
    file_path: str,
    category: str,
    status: str,
    interfaces: List[InterfaceChange],
) -> List[Tuple[str, str]]:
    """
    Generates explicitly labeled potential downstream consequences.
    Clearly marks all inferences as potential impacts, explicitly noting that
    downstream callers outside the diff were not retrieved or inspected.
    Returns: List of (label, impact_description)
    """
    impacts: List[str] = []

    # Status-based potential impacts
    if status == "deleted":
        impacts.append(
            f"Potential Impact (Inferred): Entire file '{file_path}' was removed. Any external imports referencing this module will fail (Callers outside diff were not inspected)."
        )
    elif status == "renamed":
        impacts.append(
            f"Potential Impact (Inferred): File was moved/renamed. Downstream modules importing the previous path require import path updates."
        )

    # Interface-based potential impacts
    for iface in interfaces:
        if iface.change_type == "removed_function":
            impacts.append(
                f"Potential Impact (Inferred): Function '{iface.name}' was removed. Downstream callers will encounter AttributeError or ImportError (Callers outside diff were not inspected)."
            )
        elif iface.change_type == "modified_function":
            impacts.append(
                f"Potential Impact (Inferred): Function '{iface.name}' was modified ({iface.details}). Callers may be affected if arguments or return contracts shifted."
            )
        elif iface.change_type == "added_route":
            impacts.append(
                f"Potential Impact (Inferred): Route '{iface.name}' expands public API surface and requires routing validation."
            )
        elif iface.change_type == "modified_config":
            impacts.append(
                f"Potential Impact (Inferred): Configuration setting '{iface.name}' modified. May affect runtime behavior across deployment environments."
            )

    # Category-based domain impact notes
    if category == "Authentication":
        impacts.append(
            "Potential Impact (Inferred): Auth module altered. Session verification, permission gates, or token handling across endpoints may be impacted."
        )
    elif category == "Database / Schema":
        impacts.append(
            "Potential Impact (Inferred): Database/schema changes may require migration steps and alter query assumptions in persistence layers."
        )
    elif category == "API / Contracts":
        impacts.append(
            "Potential Impact (Inferred): API contract altered. Third-party clients or frontend consumers relying on response schemas should verify backward compatibility."
        )

    # Bound to top 4 impacts per file
    return impacts[:4]


def evaluate_test_coverage_signal(files: List[FileImpact]) -> Tuple[str, bool]:
    """
    Evaluates whether test changes accompany logic/contract modifications.
    Highlights missing test changes as a signal to investigate, NOT proof of a bug.
    """
    logic_categories = {"API / Contracts", "Authentication", "Database / Schema", "Application Logic"}
    logic_files = [f for f in files if f.category in logic_categories]
    test_files = [f for f in files if f.category == "Tests"]

    if logic_files and not test_files:
        return (
            f"Missing Test Changes Signal: {len(logic_files)} application logic or contract file(s) modified, but no test files were included in this pull request. Reviewers should investigate whether existing tests adequately cover these changes.",
            True,
        )

    if logic_files and test_files:
        return (
            f"Tests Included: {len(test_files)} test file(s) updated alongside {len(logic_files)} application logic file(s).",
            False,
        )

    if test_files and not logic_files:
        return (
            f"Test-Only PR: {len(test_files)} test file(s) updated with no production logic changes.",
            False,
        )

    return (
        "Non-logic Changes: Pull request contains documentation, assets, or configuration updates only.",
        False,
    )


def build_change_impact_summary(
    parsed_files: Dict[str, ParsedFileDiff],
    findings: List[RiskFinding],
    diff_summary: DiffSummary,
) -> ChangeImpactSummary:
    """
    Assembles the bounded Change Impact Map from parsed diffs and verified findings.
    Ensures:
    - Never claims to have discovered downstream callers outside retrieved diff.
    - Does not pretend to build an omniscient dependency graph.
    - Explicitly annotates context boundaries.
    """
    file_impacts: List[FileImpact] = []
    category_counts: Dict[str, int] = {}

    for file_path, parsed in parsed_files.items():
        category = classify_file_path(file_path)
        category_counts[category] = category_counts.get(category, 0) + 1

        detected_ifaces = detect_interface_changes(parsed)
        potential_impacts = infer_potential_impacts(
            file_path=file_path,
            category=category,
            status=parsed.status,
            interfaces=detected_ifaces,
        )

        # Associate relevant findings matching this file path
        associated_findings: List[str] = []
        for finding in findings:
            for ev in finding.evidence:
                if (
                    ev.file_path == file_path
                    or ev.file_path.endswith(file_path)
                    or file_path.endswith(ev.file_path)
                ):
                    if finding.id not in associated_findings:
                        associated_findings.append(finding.id)

        file_impacts.append(
            FileImpact(
                file_path=file_path,
                status=parsed.status,
                old_path=parsed.old_path,
                category=category,
                additions=len(parsed.added_lines),
                deletions=len(parsed.deleted_lines),
                detected_interfaces=detected_ifaces,
                associated_finding_ids=associated_findings,
                potential_downstream_impacts=potential_impacts,
            )
        )

    test_signal, has_missing_tests = evaluate_test_coverage_signal(file_impacts)

    limitation_note = (
        "Context Boundary: Downstream callers and repository-wide usages outside this pull request diff were not retrieved. "
        "Potential impacts are inferred strictly from visible code modifications."
    )
    if diff_summary.truncated:
        limitation_note += (
            f" Note: Diff was bounded ({diff_summary.total_lines} lines analyzed); additional modified files may exist outside this sample."
        )

    return ChangeImpactSummary(
        total_files_analyzed=len(file_impacts),
        category_counts=category_counts,
        test_coverage_signal=test_signal,
        has_missing_tests_signal=has_missing_tests,
        context_limitation_note=limitation_note,
        files=file_impacts,
    )
