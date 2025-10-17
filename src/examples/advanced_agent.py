"""고급 Agent 예제 - 모든 기능 통합.

이 예제는 플러그인 시스템, 상태 관리, Function calling을 모두 활용하여
실용적인 AI Agent를 구현합니다.

사용 시나리오:
1. "서울 날씨 어때?" - WeatherPlugin 자동 호출
2. "Python 공식 문서 찾아줘" - search_web 도구 자동 호출  
3. "123 * 456 계산해줘" - CalculatorPlugin 자동 호출

사용 방법:
    $ uv run python examples/advanced_agent.py

지원 명령어:
    /plugins - 플러그인 목록 조회
    /enable <name> - 플러그인 활성화
    /disable <name> - 플러그인 비활성화
    /session save - 현재 세션 저장
    /session load <id> - 세션 로드
    /session list - 세션 목록
    /help - 도움말
    /quit - 종료

Example:
    >>> python examples/advanced_agent.py
    🤖 Advanced Agent started!
    You: 서울 날씨 어때?
    Assistant: 서울의 현재 날씨를 확인해드릴게요.
    [Weather plugin automatically called]
    현재 서울의 날씨는 맑음입니다. 기온은 15°C이고...
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.conversation_agent import ConversationAgent
from agent.plugins.base import PluginManager
from agent.plugins.calculator import CalculatorPlugin
from agent.plugins.weather import WeatherPlugin
from agent.state_manager import StateManager
from agent.tools.web_search import search_web
from config.agent_config import AgentConfig

# 환경 변수 로드
load_dotenv()

console = Console()


class AdvancedAgentCLI:
    """고급 Agent CLI 인터페이스.
    
    플러그인 관리, 세션 관리, 대화형 인터페이스를 제공합니다.
    """

    def __init__(self) -> None:
        """CLI를 초기화합니다."""
        self.console = console
        self.current_session_id: str | None = None
        self.plugin_manager = PluginManager()
        self.state_manager = StateManager()
        self.agent: ConversationAgent | None = None
        
        # 기본 도구 리스트
        self.available_tools = [search_web]
        
        self._setup_plugins()
        self._setup_agent()

    def _setup_plugins(self) -> None:
        """플러그인을 설정합니다."""
        try:
            # 계산기 플러그인 등록
            calc_plugin = CalculatorPlugin()
            self.plugin_manager.register_plugin(calc_plugin)
            
            # 날씨 플러그인 등록 (API 키가 있는 경우)
            weather_api_key = os.getenv("OPENWEATHER_API_KEY")
            if weather_api_key:
                weather_plugin = WeatherPlugin(weather_api_key)
                self.plugin_manager.register_plugin(weather_plugin)
            else:
                self.console.print(
                    "[yellow]⚠️  날씨 플러그인을 사용하려면 OPENWEATHER_API_KEY를 설정하세요.[/yellow]"
                )
                
        except Exception as e:
            self.console.print(f"[red]플러그인 설정 실패: {e}[/red]")

    def _setup_agent(self) -> None:
        """Agent를 설정합니다."""
        try:
            # .env 파일에서 설정 로드
            config = AgentConfig.from_env()
            
            # 시스템 메시지가 설정되지 않았으면 기본값 사용
            if not config.system_message:
                config.system_message = (
                    "당신은 도움이 되는 AI 어시스턴트입니다. "
                    "사용자의 요청에 따라 웹 검색, 계산, 날씨 조회 등의 도구를 활용하여 답변하세요."
                )
            
            # 활성화된 플러그인의 도구 함수들을 수집
            plugin_tools = []
            for plugin in self.plugin_manager.get_enabled_plugins():
                # 플러그인을 도구 함수로 변환하는 래퍼 생성
                plugin_tools.append(self._create_plugin_tool(plugin))
            
            # 전체 도구 리스트 구성
            all_tools = self.available_tools + plugin_tools
            
            self.agent = ConversationAgent(config, tools=all_tools)
            
        except Exception as e:
            self.console.print(f"[red]Agent 설정 실패: {e}[/red]")
            sys.exit(1)

    def _create_plugin_tool(self, plugin):
        """플러그인을 Microsoft Agent Framework 도구 함수로 변환합니다."""
        from typing import Annotated
        from pydantic import Field
        
        if plugin.name == "weather":
            # 날씨 플러그인용 특별 처리된 도구 함수
            def get_weather(
                location: Annotated[str, Field(description="날씨를 조회할 위치. 도시명(예: 'Seoul', '서울') 또는 좌표(예: '37.5665,126.9780') 형식으로 입력")],
                units: Annotated[str, Field(description="온도 단위 (celsius, fahrenheit, kelvin)")] = "celsius"
            ) -> str:
                """지정된 위치의 현재 날씨 정보를 조회합니다."""
                try:
                    result = plugin.execute({"location": location, "units": units})
                    
                    # 결과를 사용자 친화적인 문자열로 포맷팅
                    if isinstance(result, dict) and "temperature" in result:
                        temp_unit = "°C" if units == "celsius" else "°F" if units == "fahrenheit" else "K"
                        return (
                            f"📍 {result.get('location', location)}의 날씨 정보:\n"
                            f"🌡️ 온도: {result.get('temperature', 'N/A')}{temp_unit}\n"
                            f"☁️ 상태: {result.get('description', 'N/A')}\n"
                            f"💧 습도: {result.get('humidity', 'N/A')}%\n"
                            f"💨 풍속: {result.get('wind_speed', 'N/A')} m/s"
                        )
                    else:
                        return str(result)
                except Exception as e:
                    return f"날씨 정보 조회 실패: {e}"
            
            return get_weather
            
        elif plugin.name == "calculator":
            # 계산기 플러그인용 특별 처리된 도구 함수
            def calculate(
                expression: Annotated[str, Field(description="계산할 수식 (예: '2 + 3 * 4')")]
            ) -> str:
                """수학 계산을 수행합니다."""
                try:
                    result = plugin.execute({"expression": expression})
                    if isinstance(result, dict) and "result" in result:
                        return f"계산 결과: {expression} = {result['result']}"
                    else:
                        return str(result)
                except Exception as e:
                    return f"계산 실패: {e}"
            
            return calculate
        
        else:
            # 일반 플러그인용 기본 래퍼
            def generic_plugin_tool(**kwargs) -> str:
                """플러그인 실행 래퍼."""
                try:
                    result = plugin.execute(kwargs)
                    return str(result.get("result", result))
                except Exception as e:
                    return f"플러그인 실행 실패: {e}"
            
            # 함수 메타데이터 설정
            generic_plugin_tool.__name__ = plugin.name
            generic_plugin_tool.__doc__ = plugin.description
            
            return generic_plugin_tool

    async def run(self) -> None:
        """CLI를 실행합니다."""
        self._show_welcome()
        
        # 새 세션 생성
        self.current_session_id = self.state_manager.create_session()
        self.console.print(f"[green]새 세션 시작: {self.current_session_id}[/green]")
        
        try:
            await self._main_loop()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]👋 안녕히 가세요![/yellow]")
        finally:
            self._cleanup()

    def _show_welcome(self) -> None:
        """환영 메시지를 표시합니다."""
        welcome_text = Text()
        welcome_text.append("🤖 Advanced Agent", style="bold cyan")
        welcome_text.append("\n\n플러그인과 상태 관리를 지원하는 고급 AI Agent입니다.", style="white")
        welcome_text.append("\n'/help'를 입력하면 사용 가능한 명령어를 확인할 수 있습니다.", style="dim")
        
        panel = Panel(
            welcome_text,
            title="[bold green]환영합니다![/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(panel)

    async def _main_loop(self) -> None:
        """메인 대화 루프를 실행합니다."""
        while True:
            try:
                # 사용자 입력 받기
                user_input = Prompt.ask(
                    "\n[bold blue]You[/bold blue]",
                    console=self.console
                ).strip()
                
                if not user_input:
                    continue
                
                # 명령어 처리
                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                    continue
                
                # Agent에게 메시지 전달
                await self._chat_with_agent(user_input)
                
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]오류 발생: {e}[/red]")

    async def _handle_command(self, command: str) -> None:
        """명령어를 처리합니다."""
        parts = command[1:].split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == "help":
            self._show_help()
        elif cmd == "plugins":
            self._show_plugins()
        elif cmd == "enable":
            self._enable_plugin(args)
        elif cmd == "disable":
            self._disable_plugin(args)
        elif cmd == "session":
            await self._handle_session_command(args)
        elif cmd == "quit" or cmd == "exit":
            raise KeyboardInterrupt
        else:
            self.console.print(f"[red]알 수 없는 명령어: {command}[/red]")
            self._show_help()

    def _show_help(self) -> None:
        """도움말을 표시합니다."""
        help_table = Table(title="사용 가능한 명령어", show_header=True, header_style="bold magenta")
        help_table.add_column("명령어", style="cyan", width=20)
        help_table.add_column("설명", style="white")
        
        commands = [
            ("/help", "도움말 표시"),
            ("/plugins", "플러그인 목록 조회"),
            ("/enable <name>", "플러그인 활성화"),
            ("/disable <name>", "플러그인 비활성화"),
            ("/session save", "현재 세션 저장"),
            ("/session load <id>", "세션 로드"),
            ("/session list", "세션 목록"),
            ("/quit", "프로그램 종료"),
        ]
        
        for cmd, desc in commands:
            help_table.add_row(cmd, desc)
            
        self.console.print(help_table)

    def _show_plugins(self) -> None:
        """플러그인 목록을 표시합니다."""
        plugins = self.plugin_manager.list_plugins()
        
        if not plugins:
            self.console.print("[yellow]등록된 플러그인이 없습니다.[/yellow]")
            return
            
        plugin_table = Table(title="플러그인 목록", show_header=True, header_style="bold magenta")
        plugin_table.add_column("이름", style="cyan")
        plugin_table.add_column("설명", style="white")
        plugin_table.add_column("버전", style="green")
        plugin_table.add_column("상태", style="yellow")
        
        for plugin_info in plugins:
            status = "✅ 활성화" if plugin_info["enabled"] else "❌ 비활성화"
            plugin_table.add_row(
                plugin_info["name"],
                plugin_info["description"],
                plugin_info["version"],
                status
            )
            
        self.console.print(plugin_table)

    def _enable_plugin(self, args: list[str]) -> None:
        """플러그인을 활성화합니다."""
        if not args:
            self.console.print("[red]플러그인 이름을 입력하세요.[/red]")
            return
            
        plugin_name = args[0]
        try:
            self.plugin_manager.enable_plugin(plugin_name)
            self.console.print(f"[green]플러그인 '{plugin_name}' 활성화됨[/green]")
            self._setup_agent()  # Agent 재설정
        except Exception as e:
            self.console.print(f"[red]플러그인 활성화 실패: {e}[/red]")

    def _disable_plugin(self, args: list[str]) -> None:
        """플러그인을 비활성화합니다."""
        if not args:
            self.console.print("[red]플러그인 이름을 입력하세요.[/red]")
            return
            
        plugin_name = args[0]
        try:
            self.plugin_manager.disable_plugin(plugin_name)
            self.console.print(f"[yellow]플러그인 '{plugin_name}' 비활성화됨[/yellow]")
            self._setup_agent()  # Agent 재설정
        except Exception as e:
            self.console.print(f"[red]플러그인 비활성화 실패: {e}[/red]")

    async def _handle_session_command(self, args: list[str]) -> None:
        """세션 관련 명령어를 처리합니다."""
        if not args:
            self.console.print("[red]세션 명령어를 입력하세요 (save/load/list).[/red]")
            return
            
        subcmd = args[0].lower()
        
        if subcmd == "save":
            await self._save_session()
        elif subcmd == "load":
            if len(args) < 2:
                self.console.print("[red]로드할 세션 ID를 입력하세요.[/red]")
                return
            await self._load_session(args[1])
        elif subcmd == "list":
            self._list_sessions()
        else:
            self.console.print(f"[red]알 수 없는 세션 명령어: {subcmd}[/red]")

    async def _save_session(self) -> None:
        """현재 세션을 저장합니다."""
        if not self.current_session_id:
            self.console.print("[red]저장할 세션이 없습니다.[/red]")
            return
            
        try:
            state = self.state_manager.get_session(self.current_session_id)
            if self.agent:
                state.conversation = self.agent.conversation
            self.state_manager.update_session(self.current_session_id, state)
            self.console.print(f"[green]세션 '{self.current_session_id}' 저장됨[/green]")
        except Exception as e:
            self.console.print(f"[red]세션 저장 실패: {e}[/red]")

    async def _load_session(self, session_id: str) -> None:
        """세션을 로드합니다."""
        try:
            state = self.state_manager.get_session(session_id)
            self.current_session_id = session_id
            
            if self.agent:
                self.agent.conversation = state.conversation
                
            self.console.print(f"[green]세션 '{session_id}' 로드됨[/green]")
            self.console.print(f"[dim]메시지 수: {len(state.conversation.messages)}[/dim]")
        except Exception as e:
            self.console.print(f"[red]세션 로드 실패: {e}[/red]")

    def _list_sessions(self) -> None:
        """세션 목록을 표시합니다."""
        try:
            sessions = self.state_manager.list_sessions()
            
            if not sessions:
                self.console.print("[yellow]저장된 세션이 없습니다.[/yellow]")
                return
                
            session_table = Table(title="세션 목록", show_header=True, header_style="bold magenta")
            session_table.add_column("세션 ID", style="cyan")
            session_table.add_column("생성 시간", style="white")
            session_table.add_column("메시지 수", style="green")
            
            for session_id in sessions:
                try:
                    state = self.state_manager.get_session(session_id)
                    session_table.add_row(
                        session_id,
                        state.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        str(len(state.conversation.messages))
                    )
                except Exception:
                    continue
                    
            self.console.print(session_table)
            
        except Exception as e:
            self.console.print(f"[red]세션 목록 조회 실패: {e}[/red]")

    async def _chat_with_agent(self, user_input: str) -> None:
        """Agent와 대화합니다."""
        if not self.agent:
            self.console.print("[red]Agent가 초기화되지 않았습니다.[/red]")
            return
            
        try:
            # 타이핑 인디케이터 표시
            with self.console.status("[bold green]AI가 생각 중...", spinner="dots"):
                response = await self.agent.chat(user_input)
            
            # Agent 응답 표시
            response_text = Text()
            response_text.append("🤖 Assistant: ", style="bold green")
            response_text.append(response, style="white")
            
            self.console.print(response_text)
            
            # 현재 세션 상태 업데이트
            if self.current_session_id:
                try:
                    state = self.state_manager.get_session(self.current_session_id)
                    state.conversation = self.agent.conversation
                    self.state_manager.update_session(self.current_session_id, state)
                except Exception:
                    pass  # 세션 업데이트 실패는 무시
                    
        except Exception as e:
            self.console.print(f"[red]Agent 응답 생성 실패: {e}[/red]")

    def _cleanup(self) -> None:
        """정리 작업을 수행합니다."""
        try:
            # 마지막 세션 저장
            if self.current_session_id and self.agent:
                state = self.state_manager.get_session(self.current_session_id)
                state.conversation = self.agent.conversation
                self.state_manager.update_session(self.current_session_id, state)
                
            # 상태 관리자 정지
            self.state_manager.stop()
            
            self.console.print("[green]정리 작업 완료[/green]")
        except Exception as e:
            self.console.print(f"[yellow]정리 작업 중 오류: {e}[/yellow]")


async def main() -> None:
    """메인 함수."""
    try:
        cli = AdvancedAgentCLI()
        await cli.run()
    except Exception as e:
        console.print(f"[red]프로그램 실행 실패: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
