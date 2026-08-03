from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, kw_only=True)
class ImportReference:
    module: str
    name: str | None
    alias: str | None
    line: int

    @property
    def qualified_name(self) -> str:
        if self.name is None:
            return self.module

        if not self.module:
            return self.name

        return f"{self.module}.{self.name}"


@dataclass(frozen=True, kw_only=True)
class CallReference:
    qualified_name: str
    function_name: str | None
    line: int
    column: int

    @property
    def leaf_name(self) -> str:
        return self.qualified_name.rsplit(
            ".",
            1,
        )[-1]


@dataclass(frozen=True, kw_only=True)
class ClassReference:
    name: str
    bases: tuple[str, ...]
    line: int


@dataclass(frozen=True, kw_only=True)
class AstScanResult:
    path: Path
    imports: tuple[ImportReference, ...]
    calls: tuple[CallReference, ...]
    classes: tuple[ClassReference, ...]
    functions: tuple[str, ...]
    syntax_error: str | None = None

    @property
    def successful(self) -> bool:
        return self.syntax_error is None

    def calls_in_function(
        self,
        function_name: str,
    ) -> tuple[CallReference, ...]:
        return tuple(
            call
            for call in self.calls
            if call.function_name == function_name
        )


class _AstCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[ImportReference] = []
        self.calls: list[CallReference] = []
        self.classes: list[ClassReference] = []
        self.functions: list[str] = []
        self._function_stack: list[str] = []

    def visit_Import(
        self,
        node: ast.Import,
    ) -> None:
        for item in node.names:
            self.imports.append(
                ImportReference(
                    module=item.name,
                    name=None,
                    alias=item.asname,
                    line=node.lineno,
                )
            )

        self.generic_visit(node)

    def visit_ImportFrom(
        self,
        node: ast.ImportFrom,
    ) -> None:
        module = node.module or ""

        if node.level:
            module = (
                "." * node.level
                + module
            )

        for item in node.names:
            self.imports.append(
                ImportReference(
                    module=module,
                    name=item.name,
                    alias=item.asname,
                    line=node.lineno,
                )
            )

        self.generic_visit(node)

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:
        self.functions.append(node.name)
        self._function_stack.append(node.name)

        self.generic_visit(node)

        self._function_stack.pop()

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        self.functions.append(node.name)
        self._function_stack.append(node.name)

        self.generic_visit(node)

        self._function_stack.pop()

    def visit_Call(
        self,
        node: ast.Call,
    ) -> None:
        qualified_name = resolve_ast_name(
            node.func
        )

        if qualified_name:
            self.calls.append(
                CallReference(
                    qualified_name=qualified_name,
                    function_name=(
                        self._function_stack[-1]
                        if self._function_stack
                        else None
                    ),
                    line=node.lineno,
                    column=node.col_offset,
                )
            )

        self.generic_visit(node)

    def visit_ClassDef(
        self,
        node: ast.ClassDef,
    ) -> None:
        bases = tuple(
            name
            for name in (
                resolve_ast_name(base)
                for base in node.bases
            )
            if name
        )

        self.classes.append(
            ClassReference(
                name=node.name,
                bases=bases,
                line=node.lineno,
            )
        )

        self.generic_visit(node)


def resolve_ast_name(
    node: ast.AST,
) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = resolve_ast_name(
            node.value
        )

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    if isinstance(node, ast.Subscript):
        return resolve_ast_name(
            node.value
        )

    if isinstance(node, ast.Call):
        return resolve_ast_name(
            node.func
        )

    return None


def scan_python_file(
    path: str | Path,
) -> AstScanResult:
    source_path = Path(path)

    try:
        source = source_path.read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        return AstScanResult(
            path=source_path,
            imports=(),
            calls=(),
            classes=(),
            functions=(),
            syntax_error=(
                f"{exc.__class__.__name__}: {exc}"
            ),
        )

    try:
        tree = ast.parse(
            source,
            filename=str(source_path),
        )
    except SyntaxError as exc:
        message = (
            f"SyntaxError at line "
            f"{exc.lineno}: {exc.msg}"
        )

        return AstScanResult(
            path=source_path,
            imports=(),
            calls=(),
            classes=(),
            functions=(),
            syntax_error=message,
        )

    collector = _AstCollector()
    collector.visit(tree)

    calls = tuple(
        sorted(
            collector.calls,
            key=lambda item: (
                item.line,
                item.column,
            ),
        )
    )

    return AstScanResult(
        path=source_path,
        imports=tuple(collector.imports),
        calls=calls,
        classes=tuple(collector.classes),
        functions=tuple(collector.functions),
    )


def scan_python_files(
    paths: Iterable[str | Path],
) -> tuple[AstScanResult, ...]:
    return tuple(
        scan_python_file(path)
        for path in paths
    )


__all__ = [
    "ImportReference",
    "CallReference",
    "ClassReference",
    "AstScanResult",
    "resolve_ast_name",
    "scan_python_file",
    "scan_python_files",
]
