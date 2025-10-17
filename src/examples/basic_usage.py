"""Basic usage example using Microsoft Agent Framework.

This example demonstrates how to create and use a ChatAgent directly with
AzureOpenAIChatClient, following the official Microsoft Agent Framework patterns.

실행 방법:
    1. .env 파일 생성 및 Azure OpenAI 설정:
       AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
       AZURE_OPENAI_KEY=your-azure-openai-key
       AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4

    2. 스크립트 실행:
       python examples/basic_usage.py

예상 출력:
    === Non-Streaming Response Example ===
    User: 안녕하세요, AI Agent 테스트입니다
    Agent: 안녕하세요! 무엇을 도와드릴까요?

    === Streaming Response Example ===
    User: Python의 주요 특징 3가지를 간단히 설명해주세요
    Agent: 1. 간결한 문법...

참고:
    - Microsoft Agent Framework 공식 샘플 기반
    - https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents/azure_openai
"""

from __future__ import annotations

import asyncio
import os

from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv


async def non_streaming_example() -> None:
    """Demonstrates basic non-streaming message processing.

    Creates a simple ChatAgent and sends a single message, waiting for
    the complete response.
    """
    print("\n=== Non-Streaming Response Example ===")

    # Initialize Azure OpenAI chat client
    # Uses environment variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY
    chat_client = AzureOpenAIChatClient(
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4"),
        api_key=os.getenv("AZURE_OPENAI_KEY", None),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None)

    )

    # Create agent with instructions
    agent = chat_client.create_agent(
        name="BasicAgent",
        instructions="You are a helpful assistant. Respond concisely in Korean.",
    )

    # Send message and get response
    message = "안녕하세요, AI Agent 테스트입니다"
    print(f"User: {message}")

    result = await agent.run(message)
    print(f"Agent: {result.text}")


async def streaming_example() -> None:
    """Demonstrates streaming message processing.

    Creates a ChatAgent that streams responses, showing tokens as they arrive.
    Useful for long responses where you want to show progress.
    """
    print("\n\n=== Streaming Response Example ===")

    # Initialize client
    chat_client = AzureOpenAIChatClient( 
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4"),
        api_key=os.getenv("AZURE_OPENAI_KEY", None),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None)

    )

    # Create agent
    agent = chat_client.create_agent(
        name="StreamingAgent",
        instructions="You are a helpful assistant. Respond in Korean.",
    )

    # Send message with streaming
    message = "Python의 주요 특징 3가지를 간단히 설명해주세요"
    print(f"User: {message}")
    print("Agent: ", end="", flush=True)

    async for chunk in agent.run_stream(message):
        if chunk.text:
            print(chunk.text, end="", flush=True)

    print()  # New line after streaming


async def conversation_example() -> None:
    """Demonstrates multi-turn conversation.

    Shows how to maintain conversation context across multiple exchanges.
    The agent remembers previous messages in the conversation.
    """
    print("\n\n=== Multi-Turn Conversation Example ===")

    # Initialize client and agent
    chat_client = AzureOpenAIChatClient(
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4"),
        api_key=os.getenv("AZURE_OPENAI_KEY", None),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None)

    )
    agent = chat_client.create_agent(
        name="ConversationAgent",
        instructions="You are a helpful assistant. Respond concisely in Korean.",
    )

    # First exchange
    message1 = "제 이름은 앤디입니다"
    print(f"User: {message1}")
    result1 = await agent.run(message1)
    print(f"Agent: {result1.text}")

    # Second exchange - agent should remember the name
    message2 = "제 이름이 뭐라고 했죠?"
    print(f"\nUser: {message2}")
    result2 = await agent.run(message2)
    print(f"Agent: {result2.text}")


async def error_handling_example() -> None:
    """Demonstrates error handling with Azure OpenAI.

    Shows how to handle common errors like missing credentials,
    network issues, or API errors.
    """
    print("\n\n=== Error Handling Example ===")

    try:
        # Try to create client without proper environment variables
        temp_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        temp_key = os.getenv("AZURE_OPENAI_KEY")

        # Temporarily clear environment
        if "AZURE_OPENAI_ENDPOINT" in os.environ:
            del os.environ["AZURE_OPENAI_ENDPOINT"]
        if "AZURE_OPENAI_KEY" in os.environ:
            del os.environ["AZURE_OPENAI_KEY"]

        chat_client = AzureOpenAIChatClient()
        agent = chat_client.create_agent(
            name="ErrorAgent",
            instructions="You are a helpful assistant.",
        )

        await agent.run("test")

    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Make sure to set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY")

    except Exception as e:
        print(f"Unexpected Error: {type(e).__name__}: {e}")

    finally:
        # Restore environment variables
        if temp_endpoint:
            os.environ["AZURE_OPENAI_ENDPOINT"] = temp_endpoint
        if temp_key:
            os.environ["AZURE_OPENAI_KEY"] = temp_key


async def custom_model_example() -> None:
    """Demonstrates using a specific model/deployment.

    Shows how to specify a particular Azure OpenAI deployment
    instead of using the default from environment variables.
    """
    print("\n\n=== Custom Model Example ===")

    # Get deployment name from environment
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4")

    # Create client with explicit deployment
    chat_client = AzureOpenAIChatClient(
        deployment_name=deployment,
        api_key=os.getenv("AZURE_OPENAI_KEY", None),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None)
    )

    agent = chat_client.create_agent(
        name="CustomModelAgent",
        instructions="You are a helpful assistant. Respond in Korean.",
    )

    message = "현재 사용 중인 모델이 무엇인가요?"
    print(f"User: {message}")
    print(f"Using deployment: {deployment}")

    result = await agent.run(message)
    print(f"Agent: {result.text}")


async def main() -> None:
    """Run all examples.

    Loads environment variables and executes each example in sequence.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Verify required environment variables
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with these variables.")
        return

    print("✅ Environment variables loaded successfully")

    try:
        # Run examples
        await non_streaming_example()
        await streaming_example()
        await conversation_example()
        await error_handling_example()
        await custom_model_example()

        print("\n✅ All examples completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")

    except Exception as exc:
        print(f"\n\n❌ Error running examples: {exc}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
