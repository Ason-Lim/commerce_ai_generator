from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


SUPPORTED_EXTENSIONS = {
    ".yaml",
    ".yml",
    ".json",
}


class KnowledgeRegistryError(RuntimeError):
    """Knowledge Registry 처리 중 발생한 기본 예외."""


class KnowledgeRegistryFileNotFoundError(
    KnowledgeRegistryError
):
    """Registry 데이터 파일을 찾지 못한 경우."""


class KnowledgeRegistryFormatError(
    KnowledgeRegistryError
):
    """Registry 파일 형식 또는 최상위 구조가 잘못된 경우."""


class KnowledgeRegistryValidationError(
    KnowledgeRegistryError
):
    """Registry 데이터 검증에 실패한 경우."""


@dataclass(frozen=True)
class KnowledgeRegistryDocument:
    """
    하나의 Registry 데이터 문서를 표현한다.

    attributes:
        registry_id:
            예: beef.grades, fruit.varieties

        source_path:
            실제 데이터 파일 경로

        data:
            Registry 본문

        version:
            Registry 데이터 버전

        metadata:
            설명, 작성자, 스키마 버전 등의 부가 정보
    """

    registry_id: str
    source_path: Path
    data: dict[str, Any]
    version: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "source_path": str(self.source_path),
            "version": self.version,
            "metadata": copy.deepcopy(
                self.metadata or {}
            ),
            "data": copy.deepcopy(self.data),
        }


class KnowledgeRegistryLoader:
    """
    YAML/JSON 기반 Food Knowledge Registry Loader.

    특징:
    - YAML 및 JSON 지원
    - 메모리 캐시
    - 파일 수정 시 자동 재로딩
    - 최상위 구조 검증
    - Registry ID 기반 접근
    - 반환값 방어적 복사
    """

    def __init__(
        self,
        base_directory: str | Path | None = None,
        *,
        use_cache: bool = True,
        auto_reload: bool = True,
    ) -> None:
        self.base_directory = (
            Path(base_directory)
            if base_directory is not None
            else self.default_base_directory()
        ).resolve()

        self.use_cache = use_cache
        self.auto_reload = auto_reload

        self._cache: dict[
            Path,
            KnowledgeRegistryDocument,
        ] = {}

        self._modified_times: dict[
            Path,
            int,
        ] = {}

        self._lock = RLock()

    @staticmethod
    def default_base_directory() -> Path:
        return (
            Path(__file__)
            .resolve()
            .parent
            .parent
            / "registry_data"
        )

    def load(
        self,
        registry_id: str,
        *,
        required: bool = True,
        validate: bool = True,
        force_reload: bool = False,
    ) -> KnowledgeRegistryDocument | None:
        """
        Registry ID로 데이터를 읽는다.

        예:
            beef.grades
            fruit.varieties
        """

        source_path = self.resolve_path(
            registry_id
        )

        if source_path is None:
            if required:
                raise (
                    KnowledgeRegistryFileNotFoundError(
                        f"Registry file not found: "
                        f"{registry_id}"
                    )
                )

            return None

        return self.load_path(
            source_path,
            registry_id=registry_id,
            validate=validate,
            force_reload=force_reload,
        )

    def load_path(
        self,
        source_path: str | Path,
        *,
        registry_id: str | None = None,
        validate: bool = True,
        force_reload: bool = False,
    ) -> KnowledgeRegistryDocument:
        path = Path(source_path).resolve()

        if not path.exists():
            raise KnowledgeRegistryFileNotFoundError(
                f"Registry file not found: {path}"
            )

        if not path.is_file():
            raise KnowledgeRegistryFormatError(
                f"Registry path is not a file: {path}"
            )

        if path.suffix.lower() not in (
            SUPPORTED_EXTENSIONS
        ):
            raise KnowledgeRegistryFormatError(
                "Unsupported Registry extension: "
                f"{path.suffix}"
            )

        with self._lock:
            if (
                self.use_cache
                and not force_reload
                and self._can_use_cached(path)
            ):
                return self._copy_document(
                    self._cache[path]
                )

            raw_payload = self._read_file(path)

            normalized = (
                self._normalize_document_payload(
                    raw_payload,
                    source_path=path,
                )
            )

            resolved_registry_id = (
                registry_id
                or normalized["registry_id"]
                or self.path_to_registry_id(path)
            )

            data = normalized["data"]
            version = normalized["version"]
            metadata = normalized["metadata"]

            if validate:
                self.validate_data(
                    data,
                    registry_id=(
                        resolved_registry_id
                    ),
                )

            document = KnowledgeRegistryDocument(
                registry_id=(
                    resolved_registry_id
                ),
                source_path=path,
                data=data,
                version=version,
                metadata=metadata,
            )

            if self.use_cache:
                self._cache[path] = document
                self._modified_times[path] = (
                    path.stat().st_mtime_ns
                )

            return self._copy_document(document)

    def load_data(
        self,
        registry_id: str,
        *,
        required: bool = True,
        validate: bool = True,
        force_reload: bool = False,
    ) -> dict[str, Any] | None:
        document = self.load(
            registry_id,
            required=required,
            validate=validate,
            force_reload=force_reload,
        )

        if document is None:
            return None

        return copy.deepcopy(document.data)

    def get_entry(
        self,
        registry_id: str,
        entry_key: str,
        *,
        default: Any = None,
        required_registry: bool = True,
    ) -> Any:
        data = self.load_data(
            registry_id,
            required=required_registry,
        )

        if data is None:
            return copy.deepcopy(default)

        return copy.deepcopy(
            data.get(entry_key, default)
        )

    def list_entries(
        self,
        registry_id: str,
    ) -> list[str]:
        data = self.load_data(registry_id)

        if not data:
            return []

        return list(data.keys())

    def contains(
        self,
        registry_id: str,
        entry_key: str,
    ) -> bool:
        data = self.load_data(registry_id)

        return bool(
            data
            and entry_key in data
        )

    def resolve_path(
        self,
        registry_id: str,
    ) -> Path | None:
        """
        beef.grades를 아래 경로 후보로 변환한다.

        registry_data/beef/grades.yaml
        registry_data/beef/grades.yml
        registry_data/beef/grades.json
        """

        relative_path = Path(
            *registry_id.split(".")
        )

        for extension in (
            ".yaml",
            ".yml",
            ".json",
        ):
            candidate = (
                self.base_directory
                / relative_path
            ).with_suffix(extension)

            if candidate.is_file():
                return candidate.resolve()

        return None

    def path_to_registry_id(
        self,
        source_path: str | Path,
    ) -> str:
        path = Path(source_path).resolve()

        try:
            relative_path = path.relative_to(
                self.base_directory
            )
        except ValueError:
            relative_path = Path(path.name)

        without_suffix = relative_path.with_suffix(
            ""
        )

        return ".".join(
            without_suffix.parts
        )

    def discover(
        self,
    ) -> list[str]:
        """
        base_directory 내부의 모든 Registry ID를 반환한다.
        """

        if not self.base_directory.exists():
            return []

        registry_ids: set[str] = set()

        for extension in (
            "*.yaml",
            "*.yml",
            "*.json",
        ):
            for path in (
                self.base_directory.rglob(
                    extension
                )
            ):
                registry_ids.add(
                    self.path_to_registry_id(path)
                )

        return sorted(registry_ids)

    def validate_data(
        self,
        data: Any,
        *,
        registry_id: str,
    ) -> None:
        if not isinstance(data, Mapping):
            raise (
                KnowledgeRegistryValidationError(
                    f"{registry_id}: Registry data "
                    "must be a mapping."
                )
            )

        for entry_key, entry_value in data.items():
            if not isinstance(entry_key, str):
                raise (
                    KnowledgeRegistryValidationError(
                        f"{registry_id}: Registry "
                        "entry keys must be strings."
                    )
                )

            if not entry_key.strip():
                raise (
                    KnowledgeRegistryValidationError(
                        f"{registry_id}: Empty "
                        "entry key is not allowed."
                    )
                )

            if not isinstance(
                entry_value,
                Mapping,
            ):
                raise (
                    KnowledgeRegistryValidationError(
                        f"{registry_id}.{entry_key}: "
                        "entry value must be a mapping."
                    )
                )

    def clear_cache(
        self,
        registry_id: str | None = None,
    ) -> None:
        with self._lock:
            if registry_id is None:
                self._cache.clear()
                self._modified_times.clear()
                return

            path = self.resolve_path(registry_id)

            if path is None:
                return

            self._cache.pop(path, None)
            self._modified_times.pop(
                path,
                None,
            )

    def cache_info(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": self.use_cache,
                "auto_reload": self.auto_reload,
                "size": len(self._cache),
                "registry_ids": sorted(
                    document.registry_id
                    for document
                    in self._cache.values()
                ),
            }

    def _read_file(
        self,
        source_path: Path,
    ) -> Any:
        suffix = source_path.suffix.lower()

        with source_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            if suffix == ".json":
                try:
                    return json.load(file)
                except json.JSONDecodeError as exc:
                    raise (
                        KnowledgeRegistryFormatError(
                            "Invalid JSON Registry: "
                            f"{source_path}: {exc}"
                        )
                    ) from exc

            if suffix in {".yaml", ".yml"}:
                if yaml is None:
                    raise (
                        KnowledgeRegistryFormatError(
                            "PyYAML is required to "
                            "load YAML Registry files."
                        )
                    )

                try:
                    return (
                        yaml.safe_load(file)
                        or {}
                    )
                except yaml.YAMLError as exc:
                    raise (
                        KnowledgeRegistryFormatError(
                            "Invalid YAML Registry: "
                            f"{source_path}: {exc}"
                        )
                    ) from exc

        raise KnowledgeRegistryFormatError(
            f"Unsupported file: {source_path}"
        )

    def _normalize_document_payload(
        self,
        payload: Any,
        *,
        source_path: Path,
    ) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise KnowledgeRegistryFormatError(
                "Registry document root must be "
                f"a mapping: {source_path}"
            )

        payload_dict = dict(payload)

        # Metadata wrapper 형식:
        #
        # registry_id: beef.grades
        # version: "1.0"
        # metadata: {...}
        # data: {...}
        if "data" in payload_dict:
            data = payload_dict.get("data")

            if not isinstance(data, Mapping):
                raise (
                    KnowledgeRegistryFormatError(
                        "Registry 'data' must be a "
                        f"mapping: {source_path}"
                    )
                )

            metadata = payload_dict.get(
                "metadata"
            ) or {}

            if not isinstance(
                metadata,
                Mapping,
            ):
                raise (
                    KnowledgeRegistryFormatError(
                        "Registry 'metadata' must be "
                        f"a mapping: {source_path}"
                    )
                )

            return {
                "registry_id": (
                    payload_dict.get(
                        "registry_id"
                    )
                ),
                "version": (
                    _optional_string(
                        payload_dict.get(
                            "version"
                        )
                    )
                ),
                "metadata": dict(metadata),
                "data": dict(data),
            }

        # 단순 Registry 형식도 지원:
        #
        # 한우: {...}
        # 와규: {...}
        return {
            "registry_id": None,
            "version": None,
            "metadata": {},
            "data": payload_dict,
        }

    def _can_use_cached(
        self,
        path: Path,
    ) -> bool:
        if path not in self._cache:
            return False

        if not self.auto_reload:
            return True

        cached_mtime = self._modified_times.get(
            path
        )

        current_mtime = path.stat().st_mtime_ns

        return cached_mtime == current_mtime

    @staticmethod
    def _copy_document(
        document: KnowledgeRegistryDocument,
    ) -> KnowledgeRegistryDocument:
        return KnowledgeRegistryDocument(
            registry_id=document.registry_id,
            source_path=document.source_path,
            data=copy.deepcopy(document.data),
            version=document.version,
            metadata=copy.deepcopy(
                document.metadata or {}
            ),
        )


def _optional_string(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    return normalized or None


_default_loader = KnowledgeRegistryLoader()


def get_knowledge_registry_loader(
) -> KnowledgeRegistryLoader:
    return _default_loader


def load_knowledge_registry(
    registry_id: str,
    *,
    required: bool = True,
    validate: bool = True,
    force_reload: bool = False,
) -> KnowledgeRegistryDocument | None:
    return _default_loader.load(
        registry_id,
        required=required,
        validate=validate,
        force_reload=force_reload,
    )


def load_knowledge_registry_data(
    registry_id: str,
    *,
    required: bool = True,
    validate: bool = True,
    force_reload: bool = False,
) -> dict[str, Any] | None:
    return _default_loader.load_data(
        registry_id,
        required=required,
        validate=validate,
        force_reload=force_reload,
    )


def get_knowledge_registry_entry(
    registry_id: str,
    entry_key: str,
    *,
    default: Any = None,
) -> Any:
    return _default_loader.get_entry(
        registry_id,
        entry_key,
        default=default,
    )


def list_knowledge_registries(
) -> list[str]:
    return _default_loader.discover()


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "KnowledgeRegistryError",
    "KnowledgeRegistryFileNotFoundError",
    "KnowledgeRegistryFormatError",
    "KnowledgeRegistryValidationError",
    "KnowledgeRegistryDocument",
    "KnowledgeRegistryLoader",
    "get_knowledge_registry_loader",
    "load_knowledge_registry",
    "load_knowledge_registry_data",
    "get_knowledge_registry_entry",
    "list_knowledge_registries",
]
