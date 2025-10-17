"""웹 검색 도구 함수.

Microsoft Agent Framework 도구 패턴을 따라 구현된 웹 검색 기능을 제공합니다.
DuckDuckGo 검색 엔진을 사용하여 무료로 웹 검색을 수행합니다.
"""

import hashlib
import logging
import time
from typing import Annotated

from duckduckgo_search import DDGS
from pydantic import Field

logger = logging.getLogger(__name__)

# 검색 결과 캐시 (함수 레벨)
_search_cache: dict[str, tuple[str, float]] = {}
_cache_ttl = 3600  # 1시간


class SearchError(Exception):
    """웹 검색 관련 예외."""

    pass


def _get_cache_key(query: str, max_results: int) -> str:
    """캐시 키를 생성합니다.

    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수

    Returns:
        캐시 키
    """
    content = f"{query.lower().strip()}:{max_results}"
    return hashlib.md5(content.encode()).hexdigest()


def _is_cache_valid(timestamp: float) -> bool:
    """캐시가 유효한지 확인합니다.

    Args:
        timestamp: 캐시 생성 시간

    Returns:
        캐시 유효 여부
    """
    return time.time() - timestamp < _cache_ttl


def _format_search_results(results: list[dict]) -> str:
    """검색 결과를 포맷팅합니다.

    Args:
        results: DuckDuckGo 검색 결과 리스트

    Returns:
        포맷팅된 검색 결과 문자열
    """
    if not results:
        return "검색 결과를 찾을 수 없습니다."

    formatted_results = []
    for i, result in enumerate(results, 1):
        title = result.get("title", "제목 없음")
        url = result.get("href", "")
        snippet = result.get("body", "설명 없음")

        # 긴 snippet 자르기
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."

        formatted_result = f"{i}. **{title}**\n   URL: {url}\n   {snippet}\n"
        formatted_results.append(formatted_result)

    return "\n".join(formatted_results)


def search_web(
    query: Annotated[str, Field(description="검색할 쿼리")],
    max_results: Annotated[int, Field(description="최대 결과 수")] = 5,
) -> str:
    """DuckDuckGo를 사용하여 웹 검색을 수행합니다.

    이 함수는 Microsoft Agent Framework의 tools 패턴을 따르며,
    ChatAgent의 tools 파라미터에 직접 전달할 수 있습니다.

    Args:
        query: 검색할 쿼리 문자열
        max_results: 반환할 최대 결과 수 (기본값: 5)

    Returns:
        검색 결과를 포맷팅한 문자열 (제목, URL, 설명 포함)

    Raises:
        SearchError: 검색 실행 중 오류 발생 시

    Example:
        >>> result = search_web("Python programming", 3)
        >>> print(result)
        1. **Python Programming Tutorial**
           URL: https://example.com/python
           A comprehensive guide to Python programming...

        Agent Framework에서 사용:
        >>> from agent_framework import ChatAgent
        >>> agent = ChatAgent(
        ...     chat_client=client,
        ...     instructions="You are a helpful assistant.",
        ...     tools=[search_web]
        ... )
        >>> result = await agent.run("Search for Python tutorials")
    """
    # 입력 검증
    if not query or not query.strip():
        return "검색 쿼리가 비어있습니다."

    query = query.strip()
    max_results = max(1, min(max_results, 20))  # 1~20 사이로 제한

    # 캐시 확인
    cache_key = _get_cache_key(query, max_results)
    if cache_key in _search_cache:
        cached_result, timestamp = _search_cache[cache_key]
        if _is_cache_valid(timestamp):
            logger.info(
                "캐시에서 검색 결과 반환",
                extra={"query": query, "max_results": max_results},
            )
            return cached_result

    logger.info(
        "웹 검색 시작",
        extra={"query": query, "max_results": max_results},
    )

    try:
        # DuckDuckGo 검색 수행
        with DDGS() as ddgs:
            results = []
            search_results = ddgs.text(
                keywords=query,
                max_results=max_results,
                region="kr-kr",  # 한국 지역 설정
                safesearch="moderate",  # 안전 검색
                timelimit=None,  # 시간 제한 없음
            )

            # 결과 수집
            for result in search_results:
                if len(results) >= max_results:
                    break
                results.append(result)

        # 결과 포맷팅
        formatted_result = _format_search_results(results)

        # 캐시에 저장
        _search_cache[cache_key] = (formatted_result, time.time())

        logger.info(
            "웹 검색 완료",
            extra={
                "query": query,
                "results_count": len(results),
                "result_length": len(formatted_result),
            },
        )

        return formatted_result

    except Exception as e:
        error_msg = f"웹 검색 중 오류 발생: {str(e)}"
        logger.error(
            "웹 검색 실패",
            extra={"query": query, "error": str(e)},
        )
        raise SearchError(error_msg) from e


def clear_search_cache() -> None:
    """검색 결과 캐시를 초기화합니다.

    Example:
        >>> clear_search_cache()
        >>> len(_search_cache)
        0
    """
    global _search_cache
    _search_cache.clear()
    logger.info("검색 캐시 초기화됨")


def get_cache_stats() -> dict[str, int]:
    """캐시 통계를 반환합니다.

    Returns:
        캐시 통계 딕셔너리

    Example:
        >>> stats = get_cache_stats()
        >>> stats["total_entries"]
        5
    """
    current_time = time.time()
    valid_entries = sum(
        1
        for _, timestamp in _search_cache.values()
        if _is_cache_valid(timestamp)
    )

    return {
        "total_entries": len(_search_cache),
        "valid_entries": valid_entries,
        "expired_entries": len(_search_cache) - valid_entries,
        "cache_ttl_seconds": _cache_ttl,
    }
