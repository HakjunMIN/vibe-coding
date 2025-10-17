"""계산기 플러그인.

안전한 수식 평가를 통해 수학 계산을 수행하는 플러그인입니다.
"""

import ast
import logging
import math
import operator
from typing import Any

from .base import BasePlugin, PluginExecutionError

logger = logging.getLogger(__name__)

# 지원되는 연산자
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# 지원되는 함수
FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "pi": math.pi,
    "e": math.e,
}


class CalculatorPlugin(BasePlugin):
    """수학 계산을 수행하는 플러그인.

    안전한 AST 파싱을 사용하여 수식을 평가합니다.
    위험한 코드 실행을 방지하면서 기본적인 수학 연산과 함수를 지원합니다.

    Example:
        >>> plugin = CalculatorPlugin()
        >>> plugin.initialize()
        >>> result = plugin.execute({"expression": "2 + 3 * 4"})
        >>> result["result"]
        14.0
    """

    @property
    def name(self) -> str:
        """플러그인 이름을 반환합니다."""
        return "calculator"

    @property
    def description(self) -> str:
        """플러그인 설명을 반환합니다."""
        return "수학 계산을 안전하게 수행합니다. 기본 연산자와 수학 함수를 지원합니다."

    @property
    def version(self) -> str:
        """플러그인 버전을 반환합니다."""
        return "1.0.0"

    def initialize(self) -> None:
        """플러그인을 초기화합니다.

        계산기 플러그인은 별도의 초기화가 필요하지 않습니다.
        """
        logger.info("계산기 플러그인 초기화 완료")

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """수식을 계산합니다.

        Args:
            context: 실행 컨텍스트
                - expression (str): 계산할 수식

        Returns:
            계산 결과 딕셔너리
                - result (float): 계산 결과
                - expression (str): 원본 수식

        Raises:
            PluginExecutionError: 계산 실행 실패 시

        Example:
            >>> plugin = CalculatorPlugin()
            >>> result = plugin.execute({"expression": "sqrt(16) + 2**3"})
            >>> result["result"]
            12.0
        """
        if "expression" not in context:
            raise PluginExecutionError("expression이 필요합니다")

        expression = context["expression"]
        if not isinstance(expression, str) or not expression.strip():
            raise PluginExecutionError("유효한 수식을 입력해주세요")

        try:
            # 수식 정규화
            expression = expression.strip()
            logger.debug(f"수식 계산 시작: {expression}")

            # AST 파싱 및 계산
            result = self._safe_eval(expression)

            logger.info(
                f"수식 계산 완료: {expression} = {result}",
                extra={"expression": expression, "result": result},
            )

            return {
                "result": result,
                "expression": expression,
            }

        except Exception as e:
            logger.error(f"수식 계산 실패: {expression} - {e}")
            raise PluginExecutionError(f"계산 실패: {e}") from e

    def cleanup(self) -> None:
        """플러그인 정리 작업을 수행합니다.

        계산기 플러그인은 별도의 정리 작업이 필요하지 않습니다.
        """
        logger.info("계산기 플러그인 정리 완료")

    def get_schema(self) -> dict[str, Any]:
        """Function calling을 위한 스키마를 반환합니다.

        Returns:
            OpenAI Function calling 형식의 스키마
        """
        return {
            "name": "calculate",
            "description": "수학 계산을 수행합니다. 기본 연산자(+, -, *, /, **, %)와 "
            "수학 함수(sqrt, sin, cos, tan, log, exp, abs, round, floor, ceil)를 지원합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "계산할 수학 식. 예: '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)'",
                    }
                },
                "required": ["expression"],
            },
        }

    def _safe_eval(self, expression: str) -> float:
        """안전하게 수식을 평가합니다.

        Args:
            expression: 계산할 수식

        Returns:
            계산 결과

        Raises:
            ValueError: 잘못된 수식 또는 지원하지 않는 연산
            ZeroDivisionError: 0으로 나누기
        """
        try:
            # AST 파싱
            tree = ast.parse(expression, mode="eval")
            return self._eval_node(tree.body)

        except SyntaxError as e:
            raise ValueError(f"잘못된 수식입니다: {e}") from e

    def _eval_node(self, node: ast.AST) -> float:
        """AST 노드를 재귀적으로 평가합니다.

        Args:
            node: 평가할 AST 노드

        Returns:
            평가 결과

        Raises:
            ValueError: 지원하지 않는 노드 타입
            ZeroDivisionError: 0으로 나누기
        """
        if isinstance(node, ast.Constant):
            # 숫자 상수
            if isinstance(node.value, (int, float)):
                return float(node.value)
            else:
                raise ValueError(f"지원하지 않는 상수 타입: {type(node.value)}")

        elif isinstance(node, ast.Name):
            # 변수 (상수만 허용)
            if node.id in FUNCTIONS:
                if isinstance(FUNCTIONS[node.id], (int, float)):
                    return float(FUNCTIONS[node.id])
                else:
                    raise ValueError(f"상수가 아닌 변수는 지원하지 않습니다: {node.id}")
            else:
                raise ValueError(f"정의되지 않은 변수: {node.id}")

        elif isinstance(node, ast.BinOp):
            # 이항 연산
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)

            if op_type not in OPERATORS:
                raise ValueError(f"지원하지 않는 연산자: {op_type}")

            try:
                return OPERATORS[op_type](left, right)
            except ZeroDivisionError:
                raise ZeroDivisionError("0으로 나눌 수 없습니다")

        elif isinstance(node, ast.UnaryOp):
            # 단항 연산
            operand = self._eval_node(node.operand)
            op_type = type(node.op)

            if op_type not in OPERATORS:
                raise ValueError(f"지원하지 않는 단항 연산자: {op_type}")

            return OPERATORS[op_type](operand)

        elif isinstance(node, ast.Call):
            # 함수 호출
            if not isinstance(node.func, ast.Name):
                raise ValueError("복잡한 함수 호출은 지원하지 않습니다")

            func_name = node.func.id
            if func_name not in FUNCTIONS:
                raise ValueError(f"지원하지 않는 함수: {func_name}")

            # 함수 인자 평가
            args = [self._eval_node(arg) for arg in node.args]

            if node.keywords:
                raise ValueError("키워드 인자는 지원하지 않습니다")

            try:
                func = FUNCTIONS[func_name]
                if callable(func):
                    return float(func(*args))
                else:
                    raise ValueError(f"호출할 수 없는 객체: {func_name}")
            except Exception as e:
                raise ValueError(f"함수 실행 실패 {func_name}: {e}") from e

        else:
            raise ValueError(f"지원하지 않는 AST 노드: {type(node)}")
