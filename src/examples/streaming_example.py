"""스트리밍 응답을 보여주는 예제.

이 예제는 ConversationAgent의 chat_stream 메서드를 사용하여
실시간으로 응답을 표시합니다.

사용 방법:
    $ uv run python examples/streaming_example.py

기능:
    - 실시간 토큰 스트리밍
    - 타이핑 효과
    - 응답 시간 측정
    - 여러 질문 순차 처리
    - Rich 라이브러리 UI

Example:
    >>> python examples/streaming_example.py
    질문 1/3: 파이썬이란?
    🤖 파이썬은 고수준 프로그래밍 언어입니다...
    ⏱️  응답 시간: 2.34초
"""

import asyncio
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.text import Text

# Load environment variables from .env file
load_dotenv()

console = Console()


async def stream_response(
    agent: ChatAgent, question: str, question_num: int, total: int
) -> tuple[str, float]:
    """스트리밍 방식으로 응답을 받아 표시합니다.

    Args:
        agent: ChatAgent 인스턴스
        question: 사용자 질문
        question_num: 현재 질문 번호
        total: 전체 질문 개수

    Returns:
        완전한 응답 텍스트와 소요 시간(초)
    """
    # 질문 표시
    console.print()
    console.print(
        Panel(
            Text(question, style="bold cyan"),
            title=f"[bold yellow]질문 {question_num}/{total}[/bold yellow]",
            border_style="cyan",
        )
    )
    console.print()

    # 스트리밍 시작
    full_response = ""
    start_time = time.time()

    # Live display로 실시간 업데이트
    with Live(
        Panel(
            Text("", style="white"),
            title="[bold green]🤖 Assistant[/bold green]",
            border_style="green",
        ),
        console=console,
        refresh_per_second=10,
    ) as live:
        try:
            result = await agent.run(question)

            full_response = result.text

            # Simulate streaming for demo purposes
            for i in range(0, len(full_response), 5):
                chunk = full_response[i : i + 5]

                # Live display 업데이트
                live.update(
                    Panel(
                        Markdown(full_response[: i + 5]),
                        title="[bold green]🤖 Assistant[/bold green]",
                        border_style="green",
                    )
                )
                await asyncio.sleep(0.05)  # Simulate streaming delay

        except Exception as e:
            console.print(f"[bold red]❌ 오류 발생: {e}[/bold red]")
            return "", 0.0

    elapsed_time = time.time() - start_time

    # 응답 완료 표시
    console.print()
    console.print(
        f"[dim]⏱️  응답 시간: {elapsed_time:.2f}초 "
        f"| 토큰 수: ~{len(full_response.split())}개[/dim]"
    )

    return full_response, elapsed_time


async def run_streaming_demo() -> None:
    """스트리밍 데모를 실행합니다."""
    console.print(
        Panel.fit(
            "[bold cyan]🚀 Streaming Chat Demo[/bold cyan]\n\n"
            "실시간 스트리밍 응답을 확인하세요!",
            border_style="cyan",
        )
    )
    console.print()

    # Agent 초기화
    with console.status("[bold green]Agent 초기화 중...", spinner="dots"):
        chat_client = AzureOpenAIChatClient(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4"),
            api_key=os.getenv("AZURE_OPENAI_KEY", None),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None)
        )
        agent = ChatAgent(
            chat_client=chat_client,
            instructions="당신은 친절하고 도움이 되는 AI 어시스턴트입니다. "
            "간결하면서도 유익한 답변을 제공하세요.",
        )

    console.print("[bold green]✅ Agent 준비 완료![/bold green]")
    console.print()

    # 데모 질문들
    questions = [
        "파이썬의 주요 특징 3가지를 간단히 설명해줘.",
        "비동기 프로그래밍이란 무엇이고, 언제 사용하면 좋을까?",
        "FastAPI와 Flask의 차이점을 비교해줘.",
        "타입 힌트를 사용하면 어떤 장점이 있어?",
    ]

    total_time = 0.0
    responses = []

    # Progress bar 생성
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]질문 처리 중...", total=len(questions)
        )

        for i, question in enumerate(questions, start=1):
            response, elapsed = await stream_response(
                agent, question, i, len(questions)
            )

            if response:
                responses.append((question, response, elapsed))
                total_time += elapsed

            progress.advance(task)

            # 마지막 질문이 아니면 구분선 표시
            if i < len(questions):
                console.print()
                console.print("─" * console.width, style="dim")

    # 최종 통계
    console.print()
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]📊 세션 통계[/bold cyan]\n\n"
            f"처리된 질문: {len(responses)}/{len(questions)}개\n"
            f"총 소요 시간: {total_time:.2f}초\n"
            f"평균 응답 시간: {total_time / len(responses):.2f}초\n"
            f"총 토큰 수 (추정): ~{sum(len(r[1].split()) for r in responses)}개",
            border_style="cyan",
        )
    )

    # 대화 저장 옵션
    console.print()
    save = console.input(
        "[bold yellow]대화를 저장하시겠습니까? (y/N): [/bold yellow]"
    )

    if save.lower() in ("y", "yes"):
        filepath = Path("data/streaming_demo.json")
        try:
            # Note: Agent Framework doesn't have built-in save functionality
            # This would need custom implementation
            console.print(
                f"[bold yellow]ℹ️  대화 저장 기능은 별도 구현이 필요합니다.[/bold yellow]"
            )
        except Exception as e:
            console.print(f"[bold red]❌ 저장 실패: {e}[/bold red]")


async def run_interactive_streaming() -> None:
    """대화형 스트리밍 모드를 실행합니다."""
    console.print(
        Panel.fit(
            "[bold cyan]💬 Interactive Streaming Mode[/bold cyan]\n\n"
            "질문을 입력하면 실시간으로 응답을 받습니다.\n"
            "'exit' 또는 'quit'를 입력하면 종료됩니다.",
            border_style="cyan",
        )
    )
    console.print()

    # Agent 초기화
    chat_client = AzureOpenAIChatClient(
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4"),
        api_key=os.getenv("AZURE_OPENAI_KEY", None),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None)
    )
    agent = ChatAgent(
        chat_client=chat_client,
        instructions="당신은 친절하고 도움이 되는 AI 어시스턴트입니다.",
    )

    question_count = 0

    while True:
        console.print()
        question = console.input("[bold cyan]🧑 You: [/bold cyan]")

        if question.lower() in ("exit", "quit"):
            console.print()
            console.print("[bold yellow]👋 대화를 종료합니다.[/bold yellow]")
            break

        if not question.strip():
            continue

        question_count += 1

        # 스트리밍 응답
        await stream_response(agent, question, question_count, "?")

    # 통계 표시 (Agent Framework는 메트릭 기능이 제한적)
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]📊 세션 통계[/bold cyan]\n\n"
            f"총 질문: {question_count}개",
            border_style="cyan",
        )
    )


def main() -> None:
    """메인 함수."""
    console.print()
    console.print(
        "[bold cyan]Streaming Example - 실행 모드 선택[/bold cyan]"
    )
    console.print()
    console.print("1. 데모 모드 (미리 정의된 질문)")
    console.print("2. 대화형 모드 (자유롭게 질문)")
    console.print()

    choice = console.input("[bold yellow]선택 (1/2): [/bold yellow]")

    if choice == "1":
        asyncio.run(run_streaming_demo())
    elif choice == "2":
        asyncio.run(run_interactive_streaming())
    else:
        console.print("[bold red]잘못된 선택입니다.[/bold red]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print()
        console.print("[bold yellow]👋 프로그램을 종료합니다.[/bold yellow]")
    except Exception as e:
        console.print()
        console.print(f"[bold red]❌ 오류 발생: {e}[/bold red]")
