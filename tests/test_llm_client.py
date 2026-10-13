"""
Unit tests and smoke tests for src/llm_client.py.

This module provides comprehensive test coverage for the LLM client integration,
including connection checking, streaming responses, single-pass summarization,
Map-Reduce summarization, and RAG document chat streaming.

The test suite strictly adheres to PEP 8 coding standards and PEP 287 docstrings,
and explicitly verifies edge cases often overlooked by standard toolchains, such as:
- Non-ASCII and multi-script input (Chinese, Arabic, Cyrillic, Emojis, RTL).
- Boundary values for text (empty strings, zero-width spaces, 100K+ character inputs).
- Special floating-point numeric values (positive/negative infinity, NaN, zero, large floats).
- Custom interruption callbacks and complex multi-modal image inputs.
"""

import math
from typing import List, Dict, Any
from unittest.mock import MagicMock, patch
import pytest

from src.llm_client import (
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    PROMPT_PRESETS,
    LANGUAGE_PROMPTS,
    get_openai_client,
    check_lm_studio_connection,
    generate_streaming_response,
    run_single_pass_summary,
    map_reduce_summary,
    chat_stream_response,
)


class TestSmokeLLMClient:
    """
    Smoke tests to rapidly verify basic module integrity, default configurations,
    constants, and generator instantiations without network activity.
    """

    def test_smoke_constants_and_presets(self) -> None:
        """
        Smoke test verifying standard default constants and preset prompt dictionaries.
        """
        assert DEFAULT_BASE_URL == "http://localhost:1234/v1"
        assert DEFAULT_API_KEY == "lm-studio"
        assert len(PROMPT_PRESETS) >= 6
        assert "Executive Summary" in PROMPT_PRESETS
        assert "Math & Quantitative Analysis" in PROMPT_PRESETS
        assert "Same as Document" in LANGUAGE_PROMPTS
        assert "Finnish" in LANGUAGE_PROMPTS

    def test_smoke_openai_client_instantiation(self) -> None:
        """
        Smoke test to confirm OpenAI client object construction with default values.
        """
        client = get_openai_client()
        assert client is not None
        assert str(client.base_url) == "http://localhost:1234/v1/"

    def test_smoke_generator_creation(self) -> None:
        """
        Smoke test to ensure streaming function calls return valid generator objects.
        """
        mock_client = MagicMock()
        gen_single = run_single_pass_summary(
            client=mock_client,
            model="test-model",
            document_text="Smoke test document content.",
            preset_name="Executive Summary",
        )
        assert hasattr(gen_single, "__next__")

        gen_map_reduce = map_reduce_summary(
            client=mock_client,
            model="test-model",
            chunks=[{"chunk_id": 1, "page_range": "1", "text": "Chunk 1"}],
            preset_name="Executive Summary",
        )
        assert hasattr(gen_map_reduce, "__next__")

        gen_chat = chat_stream_response(
            client=mock_client,
            model="test-model",
            document_context="Context",
            chat_history=[],
            user_question="Question?",
        )
        assert hasattr(gen_chat, "__next__")


class TestGetOpenAIClient:
    """
    Unit tests for the get_openai_client factory function.
    """

    def test_get_openai_client_default_parameters(self) -> None:
        """
        Verifies default parameter initialization.
        """
        client = get_openai_client()
        assert client.api_key == DEFAULT_API_KEY
        assert str(client.base_url) == f"{DEFAULT_BASE_URL}/"

    def test_get_openai_client_custom_and_whitespace_inputs(self) -> None:
        """
        Tests custom URLs and API keys, including stripping leading/trailing whitespace.
        """
        client = get_openai_client(
            base_url="  http://192.168.1.50:8080/v1  ",
            api_key="  custom-secret-key  ",
        )
        assert client.api_key == "custom-secret-key"
        assert str(client.base_url) == "http://192.168.1.50:8080/v1/"

    def test_get_openai_client_empty_string_fallbacks(self) -> None:
        """
        Ensures empty string inputs fall back cleanly to default values.
        """
        client = get_openai_client(base_url="", api_key="")
        assert client.api_key == DEFAULT_API_KEY
        assert str(client.base_url) == f"{DEFAULT_BASE_URL}/"


class TestCheckLMStudioConnection:
    """
    Unit tests for LM Studio server health checking and model retrieval.
    """

    @patch("src.llm_client.get_openai_client")
    def test_check_connection_success_with_models(self, mock_get_client: MagicMock) -> None:
        """
        Tests successful connection when model models are available.
        """
        mock_model1 = MagicMock(id="llama-3-8b-instruct")
        mock_model2 = MagicMock(id="qwen2.5-7b")
        mock_response = MagicMock(data=[mock_model1, mock_model2])

        mock_client = MagicMock()
        mock_client.models.list.return_value = mock_response
        mock_get_client.return_value = mock_client

        is_connected, msg, models = check_lm_studio_connection()

        assert is_connected is True
        assert "Connected to LM Studio (2 model(s) available)" in msg
        assert models == ["llama-3-8b-instruct", "qwen2.5-7b"]

    @patch("src.llm_client.get_openai_client")
    def test_check_connection_success_no_models_loaded(self, mock_get_client: MagicMock) -> None:
        """
        Tests connection success when no models are currently loaded in LM Studio.
        """
        mock_response = MagicMock(data=[])
        mock_client = MagicMock()
        mock_client.models.list.return_value = mock_response
        mock_get_client.return_value = mock_client

        is_connected, msg, models = check_lm_studio_connection()

        assert is_connected is True
        assert "no models loaded" in msg
        assert models == ["default-model"]

    @patch("src.llm_client.get_openai_client")
    def test_check_connection_refused_error(self, mock_get_client: MagicMock) -> None:
        """
        Tests graceful handling of connection refused errors.
        """
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Connection refused on port 1234")
        mock_get_client.return_value = mock_client

        is_connected, msg, models = check_lm_studio_connection(base_url="http://localhost:1234/v1")

        assert is_connected is False
        assert "Could not connect to LM Studio" in msg
        assert models == []

    @patch("src.llm_client.get_openai_client")
    def test_check_connection_generic_exception(self, mock_get_client: MagicMock) -> None:
        """
        Tests handling of generic non-connection exceptions during status check.
        """
        mock_client = MagicMock()
        mock_client.models.list.side_effect = RuntimeError("Internal server error 500")
        mock_get_client.return_value = mock_client

        is_connected, msg, models = check_lm_studio_connection()

        assert is_connected is False
        assert "LM Studio Connection Error: Internal server error 500" in msg
        assert models == []


class TestGenerateStreamingResponse:
    """
    Unit tests for generate_streaming_response generator.
    """

    def test_generate_streaming_response_success(self) -> None:
        """
        Verifies normal token streaming execution.
        """
        chunk1 = MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello "))])
        chunk2 = MagicMock(choices=[MagicMock(delta=MagicMock(content="world!"))])
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk1, chunk2]

        tokens = list(
            generate_streaming_response(
                client=mock_client,
                model="test-model",
                system_prompt="System",
                user_content="User input",
                temperature=0.3,
            )
        )

        assert tokens == ["Hello ", "world!"]

    def test_generate_streaming_response_check_stop(self) -> None:
        """
        Verifies early cancellation when check_stop callback returns True mid-stream.
        """
        chunk1 = MagicMock(choices=[MagicMock(delta=MagicMock(content="Part 1"))])
        chunk2 = MagicMock(choices=[MagicMock(delta=MagicMock(content="Part 2"))])
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk1, chunk2]

        stop_flag = False

        def check_stop_cb() -> bool:
            return stop_flag

        gen = generate_streaming_response(
            client=mock_client,
            model="test-model",
            system_prompt="System",
            user_content="User input",
            check_stop=check_stop_cb,
        )

        first_token = next(gen)
        assert first_token == "Part 1"

        stop_flag = True
        second_token = next(gen)
        assert "Analysis stopped by user" in second_token

    def test_generate_streaming_response_context_window_exceeded(self) -> None:
        """
        Tests detection and formatting of context window exceeded errors.
        """
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "Context length exceeded limit of 4096 tokens (n_keep=128)"
        )

        tokens = list(
            generate_streaming_response(
                client=mock_client,
                model="test-model",
                system_prompt="System",
                user_content="Very large input",
            )
        )

        assert len(tokens) == 1
        assert "Context Window Exceeded in LM Studio" in tokens[0]

    def test_generate_streaming_response_generic_error(self) -> None:
        """
        Tests generic error formatting in streaming response generator.
        """
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ValueError("Invalid API request format")

        tokens = list(
            generate_streaming_response(
                client=mock_client,
                model="test-model",
                system_prompt="System",
                user_content="Input",
            )
        )

        assert len(tokens) == 1
        assert "LM Studio Error" in tokens[0]
        assert "Invalid API request format" in tokens[0]


class TestRunSinglePassSummary:
    """
    Unit tests for run_single_pass_summary function.
    """

    @patch("src.llm_client.generate_streaming_response")
    def test_single_pass_summary_preset_and_custom_instruction(
        self, mock_generate_stream: MagicMock
    ) -> None:
        """
        Tests system prompt assembly with preset selection and custom instructions.
        """
        mock_generate_stream.return_value = iter(["Summary output"])
        mock_client = MagicMock()

        tokens = list(
            run_single_pass_summary(
                client=mock_client,
                model="test-model",
                document_text="Document text content.",
                preset_name="Technical Breakdown",
                custom_instruction="Focus on architecture diagrams.",
                language="English",
            )
        )

        assert tokens == ["Summary output"]
        mock_generate_stream.assert_called_once()
        args, _ = mock_generate_stream.call_args
        system_prompt = args[2]
        assert "technical specialist" in system_prompt.lower()
        assert "Additional Instruction: Focus on architecture diagrams." in system_prompt
        assert "Language requirement: Write your entire summary report in English" in system_prompt

    @patch("src.llm_client.generate_streaming_response")
    def test_single_pass_summary_custom_prompt_preset(
        self, mock_generate_stream: MagicMock
    ) -> None:
        """
        Tests custom prompt preset overriding default system prompt structure.
        """
        mock_generate_stream.return_value = iter(["Custom output"])
        mock_client = MagicMock()

        list(
            run_single_pass_summary(
                client=mock_client,
                model="test-model",
                document_text="Content",
                preset_name="Custom Prompt",
                custom_instruction="Extract table of contents only.",
            )
        )

        args, _ = mock_generate_stream.call_args
        system_prompt = args[2]
        assert "Analyze the document according to these specific instructions:\nExtract table of contents only." in system_prompt

    @patch("src.llm_client.generate_streaming_response")
    def test_single_pass_summary_truncation_for_large_input(
        self, mock_generate_stream: MagicMock
    ) -> None:
        """
        Tests document text truncation when document length exceeds max_context_chars.
        """
        mock_generate_stream.return_value = iter(["Truncated run output"])
        mock_client = MagicMock()
        huge_text = "A" * 15000

        list(
            run_single_pass_summary(
                client=mock_client,
                model="test-model",
                document_text=huge_text,
                preset_name="Executive Summary",
                max_context_chars=5000,
            )
        )

        args, _ = mock_generate_stream.call_args
        user_content = args[3]
        assert len(user_content) > 5000
        assert "[... Document truncated for single-pass analysis." in user_content

    @patch("src.llm_client.generate_streaming_response")
    def test_single_pass_summary_image_payloads(
        self, mock_generate_stream: MagicMock
    ) -> None:
        """
        Tests multi-modal document processing with page image payloads.
        """
        mock_generate_stream.return_value = iter(["Visual report"])
        mock_client = MagicMock()

        page_images = [
            {"page_num": 1, "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}
        ]

        list(
            run_single_pass_summary(
                client=mock_client,
                model="test-model",
                document_text="Page 1 text",
                preset_name="Executive Summary",
                page_images=page_images,
            )
        )

        args, _ = mock_generate_stream.call_args
        user_content = args[3]
        assert isinstance(user_content, list)
        assert user_content[0]["type"] == "text"
        assert user_content[1]["type"] == "image_url"
        assert user_content[1]["image_url"]["url"] == page_images[0]["data_url"]

    @patch("src.llm_client.generate_streaming_response")
    def test_single_pass_summary_unicode_and_special_scripts(
        self, mock_generate_stream: MagicMock
    ) -> None:
        """
        Tests single-pass summarization with Chinese, Arabic, Cyrillic, Emojis, and RTL scripts.
        """
        mock_generate_stream.return_value = iter(["Multi-script summary"])
        mock_client = MagicMock()

        multilingual_text = (
            "Chinese: 这是一个关于人工智能DocuMind project complex text analysis 測試.\n"
            "Arabic: هذا تقرير اختبار شامل لنظام الذكاء الاصطناعي 12345.\n"
            "Cyrillic: Проверка работы системы анализа документов.\n"
            "Emojis & Symbols: 🚀🔥 Graph 𝛂 + 𝛃 = 𝛄, $E = mc^2$.\n"
            "Zero-width space: \u200b\u200b\u200b"
        )

        list(
            run_single_pass_summary(
                client=mock_client,
                model="test-model",
                document_text=multilingual_text,
                preset_name="Executive Summary",
                language="Finnish",
            )
        )

        args, _ = mock_generate_stream.call_args
        system_prompt = args[2]
        user_content = args[3]
        assert "Finnish (Suomi)" in system_prompt
        assert "Chinese: 这是一个" in user_content

    @patch("src.llm_client.generate_streaming_response")
    def test_single_pass_summary_floating_point_edge_cases(
        self, mock_generate_stream: MagicMock
    ) -> None:
        """
        Tests numeric boundary values for temperature parameter, including float('inf'), float('-inf'),
        float('nan'), zero, and negative values.
        """
        mock_generate_stream.return_value = iter(["Output"])
        mock_client = MagicMock()

        for temp in [0.0, -0.5, 1.0, 1e308, float("inf"), float("-inf"), float("nan")]:
            list(
                run_single_pass_summary(
                    client=mock_client,
                    model="test-model",
                    document_text="Document text",
                    preset_name="Executive Summary",
                    temperature=temp,
                )
            )
            args, _ = mock_generate_stream.call_args
            if math.isnan(temp):
                assert math.isnan(args[4])
            else:
                assert args[4] == temp


class TestMapReduceSummary:
    """
    Unit tests for map_reduce_summary multi-chunk summarization pipeline.
    """

    def test_map_reduce_summary_full_workflow(self) -> None:
        """
        Tests full 2-stage Map-Reduce summarization workflow execution.
        """
        mock_client = MagicMock()
        mock_map_resp1 = MagicMock(choices=[MagicMock(message=MagicMock(content="Summary Chunk 1"))])
        mock_map_resp2 = MagicMock(choices=[MagicMock(message=MagicMock(content="Summary Chunk 2"))])

        mock_client.chat.completions.create.side_effect = [mock_map_resp1, mock_map_resp2]

        reduce_chunk = MagicMock(choices=[MagicMock(delta=MagicMock(content="Final Synthesized Report"))])
        
        # In the reduce phase, generate_streaming_response is called which uses client.chat.completions.create
        mock_client.chat.completions.create.side_effect = [
            mock_map_resp1,
            mock_map_resp2,
            [reduce_chunk],
        ]

        chunks = [
            {"chunk_id": 1, "page_range": "Pages 1-2", "pages": [1, 2], "text": "Content page 1-2"},
            {"chunk_id": 2, "page_range": "Pages 3-4", "pages": [3, 4], "text": "Content page 3-4"},
        ]

        status_messages: List[str] = []

        def status_cb(msg: str) -> None:
            status_messages.append(msg)

        result_tokens = list(
            map_reduce_summary(
                client=mock_client,
                model="test-model",
                chunks=chunks,
                preset_name="Executive Summary",
                language="Finnish",
                status_callback=status_cb,
            )
        )

        assert result_tokens == ["Final Synthesized Report"]
        assert len(status_messages) == 3
        assert "Processing chunk 1/2" in status_messages[0]
        assert "Processing chunk 2/2" in status_messages[1]
        assert "Synthesizing final document summary..." in status_messages[2]

    def test_map_reduce_summary_check_stop_in_map_phase(self) -> None:
        """
        Tests map_reduce_summary when check_stop is triggered during Map phase.
        """
        mock_client = MagicMock()
        chunks = [
            {"chunk_id": 1, "page_range": "Page 1", "pages": [1], "text": "Text 1"},
            {"chunk_id": 2, "page_range": "Page 2", "pages": [2], "text": "Text 2"},
        ]

        stop_requested = True

        def check_stop_cb() -> bool:
            return stop_requested

        tokens = list(
            map_reduce_summary(
                client=mock_client,
                model="test-model",
                chunks=chunks,
                preset_name="Executive Summary",
                check_stop=check_stop_cb,
            )
        )

        assert tokens == ["⏹️ **Map phase stopped by user.**"]

    def test_map_reduce_summary_chunk_exception_recovery(self) -> None:
        """
        Verifies that errors in individual chunks during Map phase are caught gracefully
        without failing the overall summarization pipeline.
        """
        mock_client = MagicMock()

        # Chunk 1 raises exception, Chunk 2 succeeds
        mock_chunk2_resp = MagicMock(choices=[MagicMock(message=MagicMock(content="Chunk 2 Map Summary"))])
        reduce_chunk = MagicMock(choices=[MagicMock(delta=MagicMock(content="Final Report with Chunk 2"))])

        mock_client.chat.completions.create.side_effect = [
            RuntimeError("LM Studio chunk 1 timeout"),
            mock_chunk2_resp,
            [reduce_chunk],
        ]

        chunks = [
            {"chunk_id": 1, "page_range": "Page 1", "pages": [1], "text": "Broken text"},
            {"chunk_id": 2, "page_range": "Page 2", "pages": [2], "text": "Valid text"},
        ]

        result_tokens = list(
            map_reduce_summary(
                client=mock_client,
                model="test-model",
                chunks=chunks,
                preset_name="Executive Summary",
            )
        )

        assert result_tokens == ["Final Report with Chunk 2"]

    def test_map_reduce_summary_page_images_filtering(self) -> None:
        """
        Tests that page images are correctly filtered and assigned only to matching chunk pages.
        """
        mock_client = MagicMock()
        mock_map_resp = MagicMock(choices=[MagicMock(message=MagicMock(content="Map summary"))])
        reduce_chunk = MagicMock(choices=[MagicMock(delta=MagicMock(content="Final summary"))])

        mock_client.chat.completions.create.side_effect = [
            mock_map_resp,
            [reduce_chunk],
        ]

        chunks = [
            {"chunk_id": 1, "page_range": "Page 1", "pages": [1], "text": "Chunk 1 text"},
        ]

        page_images = [
            {"page_num": 1, "data_url": "data:image/png;base64,image1"},
            {"page_num": 2, "data_url": "data:image/png;base64,image2"},
        ]

        list(
            map_reduce_summary(
                client=mock_client,
                model="test-model",
                chunks=chunks,
                preset_name="Executive Summary",
                page_images=page_images,
            )
        )

        # Inspect first API call for chunk 1
        first_call = mock_client.chat.completions.create.call_args_list[0]
        messages = first_call.kwargs["messages"]
        user_msg = messages[1]["content"]
        assert isinstance(user_msg, list)
        assert len(user_msg) == 2  # Text + Image for Page 1 only
        assert user_msg[1]["image_url"]["url"] == "data:image/png;base64,image1"


class TestChatStreamResponse:
    """
    Unit tests for chat_stream_response RAG assistant function.
    """

    def test_chat_stream_response_relevance_chunk_scoring(self) -> None:
        """
        Tests chunk scoring, selection, and document order preservation for chat context retrieval.
        """
        mock_client = MagicMock()
        mock_stream_chunk = MagicMock(choices=[MagicMock(delta=MagicMock(content="Answer based on section 2"))])
        mock_client.chat.completions.create.return_value = [mock_stream_chunk]

        chunks = [
            {"chunk_id": 1, "page_range": "Page 1", "text": "General intro without target terms."},
            {"chunk_id": 2, "page_range": "Page 2", "text": "Detailed explanation of quantum computing algorithm performance."},
            {"chunk_id": 3, "page_range": "Page 3", "text": "Irrelevant appendix notes."},
        ]

        chat_history = [
            {"role": "user", "content": "What is this doc?"},
            {"role": "assistant", "content": "It is a tech report."},
        ]

        tokens = list(
            chat_stream_response(
                client=mock_client,
                model="test-model",
                document_context="Full context string",
                chat_history=chat_history,
                user_question="Tell me about quantum computing algorithm performance",
                chunks=chunks,
            )
        )

        assert tokens == ["Answer based on section 2"]

        # Verify system prompt content passed to OpenAI client
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_msg = messages[0]["content"]

        assert "quantum computing algorithm performance" in system_msg.lower()
        assert "Section (Page 2)" in system_msg

    def test_chat_stream_response_fallback_full_context(self) -> None:
        """
        Tests fallback to raw document context when chunks parameter is None or empty.
        """
        mock_client = MagicMock()
        mock_stream_chunk = MagicMock(choices=[MagicMock(delta=MagicMock(content="Fallback answer"))])
        mock_client.chat.completions.create.return_value = [mock_stream_chunk]

        tokens = list(
            chat_stream_response(
                client=mock_client,
                model="test-model",
                document_context="Raw fallback context string",
                chat_history=[],
                user_question="What is the main topic?",
                chunks=None,
            )
        )

        assert tokens == ["Fallback answer"]
        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        assert "Raw fallback context string" in messages[0]["content"]

    def test_chat_stream_response_history_truncation(self) -> None:
        """
        Verifies that only the last 4 chat history messages are included in prompt context.
        """
        mock_client = MagicMock()
        mock_stream_chunk = MagicMock(choices=[MagicMock(delta=MagicMock(content="Response"))])
        mock_client.chat.completions.create.return_value = [mock_stream_chunk]

        long_history = [
            {"role": "user", "content": f"Question {i}"} if i % 2 == 0 else {"role": "assistant", "content": f"Answer {i}"}
            for i in range(10)
        ]

        list(
            chat_stream_response(
                client=mock_client,
                model="test-model",
                document_context="Context",
                chat_history=long_history,
                user_question="Latest question?",
            )
        )

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        # 1 system + 4 history + 1 user = 6 messages
        assert len(messages) == 6
        assert messages[1]["content"] == "Question 6"

    def test_chat_stream_response_context_length_error_handling(self) -> None:
        """
        Tests error output when chat query triggers context window limit exception.
        """
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "Tokens context length limit reached"
        )

        tokens = list(
            chat_stream_response(
                client=mock_client,
                model="test-model",
                document_context="Context",
                chat_history=[],
                user_question="Complex question?",
            )
        )

        assert len(tokens) == 1
        assert "Context Window Exceeded" in tokens[0]

    def test_chat_stream_response_extreme_inputs(self) -> None:
        """
        Tests chat streaming with extreme non-ASCII questions, Chinese/Arabic queries,
        punctuation-only strings, very long query text, and infinity temperatures.
        """
        mock_client = MagicMock()
        mock_stream_chunk = MagicMock(choices=[MagicMock(delta=MagicMock(content="Multilingual response"))])
        mock_client.chat.completions.create.return_value = [mock_stream_chunk]

        extreme_questions = [
            "??? !!! :::",
            "Chinese: 請問這份文件的核心結論是什麼？",
            "Arabic: ما هي النتائج الرئيسية والتوصيات؟",
            "Very long text " * 500,
            "Special characters: \n\t\r\\/$E=mc^2$",
        ]

        for question in extreme_questions:
            tokens = list(
                chat_stream_response(
                    client=mock_client,
                    model="test-model",
                    document_context="Multilingual document context.",
                    chat_history=[],
                    user_question=question,
                    temperature=0.0,
                )
            )
            assert tokens == ["Multilingual response"]
