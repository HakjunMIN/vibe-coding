"""Agent 플러그인 시스템의 기본 클래스와 매니저."""

import importlib.util
import inspect
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """플러그인 관련 예외의 기본 클래스."""

    pass


class PluginLoadError(PluginError):
    """플러그인 로드 실패 시 발생하는 예외."""

    pass


class PluginExecutionError(PluginError):
    """플러그인 실행 실패 시 발생하는 예외."""

    pass


class BasePlugin(ABC):
    """Agent 플러그인의 기본 추상 클래스.

    모든 플러그인은 이 클래스를 상속받아 구현해야 합니다.

    Attributes:
        enabled: 플러그인 활성화 상태

    Example:
        >>> class MyPlugin(BasePlugin):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_plugin"
        ...
        ...     def initialize(self) -> None:
        ...         pass
        ...
        ...     def execute(self, context: dict) -> dict:
        ...         return {"result": "success"}
    """

    def __init__(self) -> None:
        """BasePlugin을 초기화합니다."""
        self.enabled = True

    @property
    @abstractmethod
    def name(self) -> str:
        """플러그인의 고유 이름을 반환합니다.

        Returns:
            플러그인 이름
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """플러그인의 설명을 반환합니다.

        Returns:
            플러그인 설명
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """플러그인의 버전을 반환합니다.

        Returns:
            플러그인 버전 (예: "1.0.0")
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """플러그인을 초기화합니다.

        플러그인 로드 시 한 번 호출됩니다.
        필요한 리소스 초기화, 설정 로드 등을 수행합니다.

        Raises:
            PluginError: 초기화 실패 시
        """
        pass

    @abstractmethod
    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """플러그인을 실행합니다.

        Args:
            context: 실행 컨텍스트 정보

        Returns:
            실행 결과 딕셔너리

        Raises:
            PluginExecutionError: 실행 실패 시
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """플러그인 정리 작업을 수행합니다.

        플러그인 언로드 시 호출됩니다.
        리소스 해제, 연결 종료 등을 수행합니다.
        """
        pass

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Function calling을 위한 플러그인 스키마를 반환합니다.

        Returns:
            OpenAI Function calling 형식의 스키마

        Example:
            >>> {
            ...     "name": "search_web",
            ...     "description": "Search the web for information",
            ...     "parameters": {
            ...         "type": "object",
            ...         "properties": {
            ...             "query": {
            ...                 "type": "string",
            ...                 "description": "Search query"
            ...             }
            ...         },
            ...         "required": ["query"]
            ...     }
            ... }
        """
        pass


class PluginManager:
    """플러그인을 관리하는 매니저 클래스.

    플러그인의 등록, 해제, 실행을 담당합니다.

    Attributes:
        plugins: 등록된 플러그인 딕셔너리

    Example:
        >>> manager = PluginManager()
        >>> plugin = MyPlugin()
        >>> manager.register_plugin(plugin)
        >>> result = manager.execute_plugin("my_plugin", {"input": "test"})
    """

    def __init__(self) -> None:
        """PluginManager를 초기화합니다."""
        self.plugins: dict[str, BasePlugin] = {}
        logger.info("PluginManager 초기화됨")

    def register_plugin(self, plugin: BasePlugin) -> None:
        """플러그인을 등록합니다.

        Args:
            plugin: 등록할 플러그인

        Raises:
            PluginError: 플러그인 등록 실패 시

        Example:
            >>> manager = PluginManager()
            >>> plugin = MyPlugin()
            >>> manager.register_plugin(plugin)
        """
        try:
            # 플러그인 검증
            self._validate_plugin(plugin)

            # 중복 확인
            if plugin.name in self.plugins:
                logger.warning(f"플러그인 '{plugin.name}' 이미 등록됨 - 덮어쓰기")

            # 초기화
            plugin.initialize()

            # 등록
            self.plugins[plugin.name] = plugin

            logger.info(
                f"플러그인 등록 완료: {plugin.name} v{plugin.version}",
                extra={
                    "plugin_name": plugin.name,
                    "plugin_version": plugin.version,
                    "enabled": plugin.enabled,
                },
            )

        except Exception as e:
            logger.error(f"플러그인 등록 실패: {plugin.name} - {e}")
            raise PluginError(f"플러그인 등록 실패: {e}") from e

    def unregister_plugin(self, name: str) -> None:
        """플러그인을 해제합니다.

        Args:
            name: 해제할 플러그인 이름

        Raises:
            PluginError: 플러그인이 존재하지 않는 경우

        Example:
            >>> manager.unregister_plugin("my_plugin")
        """
        if name not in self.plugins:
            raise PluginError(f"플러그인을 찾을 수 없습니다: {name}")

        try:
            plugin = self.plugins[name]
            plugin.cleanup()
            del self.plugins[name]

            logger.info(f"플러그인 해제 완료: {name}")

        except Exception as e:
            logger.error(f"플러그인 해제 실패: {name} - {e}")
            raise PluginError(f"플러그인 해제 실패: {e}") from e

    def get_plugin(self, name: str) -> BasePlugin:
        """플러그인을 조회합니다.

        Args:
            name: 조회할 플러그인 이름

        Returns:
            플러그인 인스턴스

        Raises:
            PluginError: 플러그인이 존재하지 않는 경우

        Example:
            >>> plugin = manager.get_plugin("my_plugin")
        """
        if name not in self.plugins:
            raise PluginError(f"플러그인을 찾을 수 없습니다: {name}")

        return self.plugins[name]

    def list_plugins(self) -> list[dict[str, Any]]:
        """등록된 모든 플러그인 목록을 반환합니다.

        Returns:
            플러그인 정보 리스트

        Example:
            >>> plugins = manager.list_plugins()
            >>> for plugin in plugins:
            ...     print(f"{plugin['name']}: {plugin['description']}")
        """
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "enabled": plugin.enabled,
            }
            for plugin in self.plugins.values()
        ]

    def execute_plugin(self, name: str, context: dict[str, Any]) -> dict[str, Any]:
        """플러그인을 실행합니다.

        Args:
            name: 실행할 플러그인 이름
            context: 실행 컨텍스트

        Returns:
            실행 결과

        Raises:
            PluginError: 플러그인이 존재하지 않거나 실행 실패 시

        Example:
            >>> result = manager.execute_plugin("my_plugin", {"input": "test"})
        """
        if name not in self.plugins:
            raise PluginError(f"플러그인을 찾을 수 없습니다: {name}")

        plugin = self.plugins[name]

        if not plugin.enabled:
            raise PluginError(f"플러그인이 비활성화됨: {name}")

        try:
            logger.debug(f"플러그인 실행 시작: {name}", extra={"context": context})

            result = plugin.execute(context)

            logger.debug(
                f"플러그인 실행 완료: {name}",
                extra={"result_keys": list(result.keys()) if result else []},
            )

            return result

        except Exception as e:
            logger.error(f"플러그인 실행 실패: {name} - {e}")
            raise PluginExecutionError(f"플러그인 실행 실패: {e}") from e

    def load_from_directory(self, path: str | Path) -> list[str]:
        """디렉토리에서 플러그인을 로드합니다.

        Args:
            path: 플러그인 디렉토리 경로

        Returns:
            로드된 플러그인 이름 리스트

        Example:
            >>> loaded = manager.load_from_directory("plugins/")
            >>> print(f"로드된 플러그인: {loaded}")
        """
        path = Path(path)
        loaded_plugins = []

        if not path.exists() or not path.is_dir():
            logger.warning(f"플러그인 디렉토리를 찾을 수 없습니다: {path}")
            return loaded_plugins

        for py_file in path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                plugins = self._load_plugins_from_file(py_file)
                loaded_plugins.extend(plugins)

            except Exception as e:
                logger.error(f"플러그인 파일 로드 실패: {py_file} - {e}")
                continue

        logger.info(
            f"디렉토리에서 플러그인 로드 완료: {len(loaded_plugins)}개",
            extra={"directory": str(path), "plugins": loaded_plugins},
        )

        return loaded_plugins

    def _validate_plugin(self, plugin: BasePlugin) -> None:
        """플러그인을 검증합니다.

        Args:
            plugin: 검증할 플러그인

        Raises:
            PluginError: 검증 실패 시
        """
        if not isinstance(plugin, BasePlugin):
            raise PluginError("BasePlugin을 상속받지 않음")

        # 필수 속성 확인
        try:
            _ = plugin.name
            _ = plugin.description
            _ = plugin.version
        except Exception as e:
            raise PluginError(f"필수 속성 누락: {e}") from e

        # 스키마 검증
        try:
            schema = plugin.get_schema()
            if not isinstance(schema, dict) or "name" not in schema:
                raise PluginError("유효하지 않은 스키마 형식")
        except Exception as e:
            raise PluginError(f"스키마 검증 실패: {e}") from e

    def _load_plugins_from_file(self, file_path: Path) -> list[str]:
        """파일에서 플러그인을 로드합니다.

        Args:
            file_path: 플러그인 파일 경로

        Returns:
            로드된 플러그인 이름 리스트

        Raises:
            PluginLoadError: 로드 실패 시
        """
        try:
            spec = importlib.util.spec_from_file_location(
                file_path.stem, file_path
            )
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"모듈 spec 생성 실패: {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            loaded_plugins = []

            # 모듈에서 BasePlugin 서브클래스 찾기
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BasePlugin)
                    and obj is not BasePlugin
                    and obj.__module__ == module.__name__
                ):
                    try:
                        plugin_instance = obj()
                        self.register_plugin(plugin_instance)
                        loaded_plugins.append(plugin_instance.name)

                    except Exception as e:
                        logger.error(f"플러그인 인스턴스 생성 실패: {name} - {e}")
                        continue

            return loaded_plugins

        except Exception as e:
            raise PluginLoadError(f"파일 로드 실패: {file_path} - {e}") from e

    def enable_plugin(self, name: str) -> None:
        """플러그인을 활성화합니다.

        Args:
            name: 활성화할 플러그인 이름

        Raises:
            PluginError: 플러그인이 존재하지 않는 경우
        """
        plugin = self.get_plugin(name)
        plugin.enabled = True
        logger.info(f"플러그인 활성화: {name}")

    def disable_plugin(self, name: str) -> None:
        """플러그인을 비활성화합니다.

        Args:
            name: 비활성화할 플러그인 이름

        Raises:
            PluginError: 플러그인이 존재하지 않는 경우
        """
        plugin = self.get_plugin(name)
        plugin.enabled = False
        logger.info(f"플러그인 비활성화: {name}")

    def get_enabled_plugins(self) -> list[BasePlugin]:
        """활성화된 플러그인 목록을 반환합니다.

        Returns:
            활성화된 플러그인 리스트
        """
        return [plugin for plugin in self.plugins.values() if plugin.enabled]

    def get_schemas(self) -> list[dict[str, Any]]:
        """모든 활성화된 플러그인의 스키마를 반환합니다.

        Returns:
            플러그인 스키마 리스트 (Function calling용)
        """
        schemas = []
        for plugin in self.get_enabled_plugins():
            try:
                schema = plugin.get_schema()
                schemas.append(schema)
            except Exception as e:
                logger.error(f"플러그인 스키마 조회 실패: {plugin.name} - {e}")
                continue

        return schemas
