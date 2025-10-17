"""날씨 정보 플러그인.

OpenWeatherMap API를 사용하여 실시간 날씨 정보를 제공하는 플러그인입니다.
"""

import asyncio
import logging
import re
import time
from typing import Any

import httpx

from .base import BasePlugin, PluginError, PluginExecutionError

logger = logging.getLogger(__name__)

# 캐시 TTL (1시간)
CACHE_TTL = 3600

# 온도 단위
TEMPERATURE_UNITS = {
    "celsius": "metric",
    "fahrenheit": "imperial",
    "kelvin": "standard",
}


class WeatherPlugin(BasePlugin):
    """날씨 정보를 제공하는 플러그인.

    OpenWeatherMap API를 사용하여 현재 날씨 정보를 조회합니다.
    결과를 캐싱하여 API 호출을 최소화합니다.

    Attributes:
        api_key: OpenWeatherMap API 키
        base_url: API 기본 URL
        default_units: 기본 온도 단위
        cache: 날씨 정보 캐시

    Example:
        >>> plugin = WeatherPlugin(api_key="your_api_key")
        >>> plugin.initialize()
        >>> result = plugin.execute({"location": "Seoul"})
        >>> result["temperature"]
        15.5
    """

    def __init__(self, api_key: str, default_units: str = "celsius") -> None:
        """WeatherPlugin을 초기화합니다.

        Args:
            api_key: OpenWeatherMap API 키
            default_units: 기본 온도 단위 ("celsius", "fahrenheit", "kelvin")

        Raises:
            PluginError: API 키가 없거나 잘못된 단위인 경우
        """
        super().__init__()

        if not api_key or not api_key.strip():
            raise PluginError("OpenWeatherMap API 키가 필요합니다")

        if default_units not in TEMPERATURE_UNITS:
            raise PluginError(
                f"지원하지 않는 온도 단위: {default_units}. "
                f"지원 단위: {list(TEMPERATURE_UNITS.keys())}"
            )

        self.api_key = api_key.strip()
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.default_units = default_units
        self.cache: dict[str, tuple[dict[str, Any], float]] = {}

    @property
    def name(self) -> str:
        """플러그인 이름을 반환합니다."""
        return "weather"

    @property
    def description(self) -> str:
        """플러그인 설명을 반환합니다."""
        return "OpenWeatherMap API를 사용하여 현재 날씨 정보를 제공합니다."

    @property
    def version(self) -> str:
        """플러그인 버전을 반환합니다."""
        return "1.0.0"

    def initialize(self) -> None:
        """플러그인을 초기화합니다.

        API 키 유효성을 간단히 확인합니다.
        """
        logger.info(
            "날씨 플러그인 초기화 완료",
            extra={"default_units": self.default_units},
        )

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """날씨 정보를 조회합니다.

        Args:
            context: 실행 컨텍스트
                - location (str): 위치 (도시명 또는 좌표)
                - units (str, optional): 온도 단위

        Returns:
            날씨 정보 딕셔너리
                - location (str): 위치
                - temperature (float): 온도
                - description (str): 날씨 설명
                - humidity (int): 습도 (%)
                - wind_speed (float): 풍속

        Raises:
            PluginExecutionError: 날씨 조회 실패 시

        Example:
            >>> result = plugin.execute({
            ...     "location": "Seoul",
            ...     "units": "celsius"
            ... })
            >>> result["temperature"]
            15.5
        """
        if "location" not in context:
            raise PluginExecutionError("location이 필요합니다")

        location = context["location"]
        if not isinstance(location, str) or not location.strip():
            raise PluginExecutionError("유효한 위치를 입력해주세요")

        units = context.get("units", self.default_units)
        if units not in TEMPERATURE_UNITS:
            units = self.default_units

        try:
            # 위치 정규화
            normalized_location = self._normalize_location(location.strip())

            # 캐시 확인
            cache_key = f"{normalized_location}:{units}"
            cached_data = self._get_cached_weather(cache_key)
            if cached_data:
                logger.info(f"캐시에서 날씨 정보 반환: {normalized_location}")
                return cached_data

            logger.debug(f"날씨 조회 시작: {normalized_location}")

            # 비동기 실행을 위한 이벤트 루프 처리
            try:
                # 현재 이벤트 루프가 실행 중인지 확인
                asyncio.get_running_loop()
                # 이미 실행 중인 루프가 있으면 별도 스레드에서 실행
                # concurrent.futures를 사용하여 별도 스레드에서 실행
                import concurrent.futures

                def run_async():
                    """새로운 스레드에서 비동기 함수 실행"""
                    return asyncio.run(
                        self._fetch_weather_async(normalized_location, units)
                    )

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async)
                    result = future.result(timeout=30)  # 30초 타임아웃

            except RuntimeError:
                # 실행 중인 루프가 없으면 새 루프 생성
                result = asyncio.run(
                    self._fetch_weather_async(normalized_location, units)
                )

            # 캐시에 저장
            self._cache_weather(cache_key, result)

            logger.info(
                f"날씨 조회 완료: {normalized_location}",
                extra={"location": normalized_location, "temperature": result["temperature"]},
            )

            return result

        except Exception as e:
            logger.error(f"날씨 조회 실패: {location} - {e}")
            raise PluginExecutionError(f"날씨 조회 실패: {e}") from e

    async def _fetch_weather_async(
        self, location: str, units: str
    ) -> dict[str, Any]:
        """비동기적으로 날씨 정보를 가져옵니다.

        Args:
            location: 정규화된 위치
            units: 온도 단위

        Returns:
            날씨 정보 딕셔너리

        Raises:
            PluginExecutionError: API 호출 실패 시
        """
        params = {
            "q": location,
            "appid": self.api_key,
            "units": TEMPERATURE_UNITS[units],
            "lang": "kr",  # 한국어 설명
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)

                if response.status_code == 401:
                    raise PluginExecutionError("잘못된 API 키입니다")
                elif response.status_code == 404:
                    raise PluginExecutionError(f"위치를 찾을 수 없습니다: {location}")
                elif response.status_code != 200:
                    raise PluginExecutionError(
                        f"API 호출 실패: {response.status_code}"
                    )

                data = response.json()
                return self._parse_weather_data(data, location, units)

        except httpx.RequestError as e:
            raise PluginExecutionError(f"네트워크 오류: {e}") from e

    def _parse_weather_data(
        self, data: dict[str, Any], location: str, units: str
    ) -> dict[str, Any]:
        """API 응답 데이터를 파싱합니다.

        Args:
            data: OpenWeatherMap API 응답
            location: 요청한 위치
            units: 온도 단위

        Returns:
            파싱된 날씨 정보
        """
        return {
            "location": data.get("name", location),
            "temperature": round(data["main"]["temp"], 1),
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": round(data.get("wind", {}).get("speed", 0), 1),
            "units": units,
        }

    def _normalize_location(self, location: str) -> str:
        """위치 문자열을 정규화합니다.

        Args:
            location: 원본 위치

        Returns:
            정규화된 위치

        Example:
            >>> plugin._normalize_location("서울특별시")
            "Seoul"
            >>> plugin._normalize_location("37.5665,126.9780")
            "37.5665,126.9780"
        """
        # 좌표 형식 확인 (위도,경도)
        coord_pattern = r"^-?\d+\.?\d*,-?\d+\.?\d*$"
        if re.match(coord_pattern, location.replace(" ", "")):
            return location.replace(" ", "")

        # 한국 도시명 영어 변환
        korean_cities = {
            "서울": "Seoul",
            "서울특별시": "Seoul",
            "부산": "Busan",
            "부산광역시": "Busan",
            "인천": "Incheon",
            "인천광역시": "Incheon",
            "대구": "Daegu",
            "대구광역시": "Daegu",
            "대전": "Daejeon",
            "대전광역시": "Daejeon",
            "광주": "Gwangju",
            "광주광역시": "Gwangju",
            "울산": "Ulsan",
            "울산광역시": "Ulsan",
        }

        return korean_cities.get(location, location)

    def _get_cached_weather(self, cache_key: str) -> dict[str, Any] | None:
        """캐시에서 날씨 정보를 가져옵니다.

        Args:
            cache_key: 캐시 키

        Returns:
            캐시된 날씨 정보 또는 None
        """
        if cache_key in self.cache:
            weather_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < CACHE_TTL:
                return weather_data

            # 만료된 캐시 제거
            del self.cache[cache_key]

        return None

    def _cache_weather(self, cache_key: str, weather_data: dict[str, Any]) -> None:
        """날씨 정보를 캐시에 저장합니다.

        Args:
            cache_key: 캐시 키
            weather_data: 날씨 정보
        """
        self.cache[cache_key] = (weather_data, time.time())

    def cleanup(self) -> None:
        """플러그인 정리 작업을 수행합니다.

        캐시를 초기화합니다.
        """
        self.cache.clear()
        logger.info("날씨 플러그인 정리 완료")

    def get_schema(self) -> dict[str, Any]:
        """Function calling을 위한 스키마를 반환합니다.

        Returns:
            OpenAI Function calling 형식의 스키마
        """
        return {
            "name": "get_weather",
            "description": "지정된 위치의 현재 날씨 정보를 조회합니다. "
            "도시명 또는 좌표(위도,경도)를 입력할 수 있습니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "날씨를 조회할 위치. 도시명(예: 'Seoul', '서울') 또는 "
                        "좌표(예: '37.5665,126.9780') 형식으로 입력",
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit", "kelvin"],
                        "description": "온도 단위 (기본값: celsius)",
                        "default": "celsius",
                    },
                },
                "required": ["location"],
            },
        }

    def clear_cache(self) -> None:
        """날씨 캐시를 초기화합니다.

        Example:
            >>> plugin.clear_cache()
        """
        self.cache.clear()
        logger.info("날씨 캐시 초기화됨")

    def get_cache_stats(self) -> dict[str, int]:
        """캐시 통계를 반환합니다.

        Returns:
            캐시 통계 딕셔너리

        Example:
            >>> stats = plugin.get_cache_stats()
            >>> stats["total_entries"]
            5
        """
        current_time = time.time()
        valid_entries = sum(
            1
            for _, timestamp in self.cache.values()
            if current_time - timestamp < CACHE_TTL
        )

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_ttl_seconds": CACHE_TTL,
        }
