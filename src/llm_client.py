from typing import List, Dict, Any, Generator, Optional, Tuple
import openai
from openai import OpenAI

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_API_KEY = "lm-studio"

PROMPT_PRESETS = {
    "Executive Summary": (
        "You are an expert document analyst. Provide a comprehensive Executive Summary of the provided document.\n"
        "Structure your output using clear Markdown headings:\n"
        "1. **Core Purpose & Overview**: 2-3 paragraphs summarizing what the document is about.\n"
        "2. **Main Themes & Objectives**: Highlight the central concepts.\n"
        "3. **Key Conclusions**: Summarize the final outcomes or statements."
    ),
    "Key Insights & Bullet Points": (
        "You are an executive assistant. Extract the top 7-10 most important key insights, facts, or findings from the document.\n"
        "Format as bullet points with bold titles for each point. Be precise, concise, and clear."
    ),
    "Technical Breakdown": (
        "You are a technical specialist. Analyze the document for technical details, methodologies, architectures, algorithms, data structures, or quantitative results.\n"
        "Provide a structured technical report detailing the methodologies, specifications, and performance numbers mentioned."
    ),
    "Actionable Takeaways & Next Steps": (
        "You are a strategic advisor. Extract all actionable recommendations, requirements, decisions, and proposed next steps from the document.\n"
        "Categorize them into clear action items."
    ),
    "Custom Prompt": (
        "You are a helpful AI assistant reading a PDF document. Answer the user's instructions accurately based strictly on the document text."
    )
}

def get_openai_client(base_url: str = DEFAULT_BASE_URL, api_key: str = DEFAULT_API_KEY) -> OpenAI:
    """
    Returns an OpenAI client configured for local LM Studio endpoint.
    """
    clean_url = base_url.strip() if base_url else DEFAULT_BASE_URL
    clean_key = api_key.strip() if api_key else DEFAULT_API_KEY
    return OpenAI(base_url=clean_url, api_key=clean_key)

def check_lm_studio_connection(base_url: str = DEFAULT_BASE_URL, api_key: str = DEFAULT_API_KEY) -> Tuple[bool, str, List[str]]:
    """
    Tests connection to LM Studio local server and retrieves loaded model IDs.
    Returns (is_connected, status_message, list_of_models).
    """
    try:
        client = get_openai_client(base_url=base_url, api_key=api_key)
        models_response = client.models.list()
        model_ids = [m.id for m in models_response.data] if models_response.data else []
        
        if not model_ids:
            return True, "Connected to LM Studio server (no models loaded in LM Studio yet).", ["default-model"]
            
        return True, f"Connected to LM Studio ({len(model_ids)} model(s) available)", model_ids
    except Exception as e:
        err_msg = str(e)
        if "Connection refused" in err_msg or "Failed to connect" in err_msg or "ConnectError" in err_msg:
            return False, f"Could not connect to LM Studio at {base_url}. Ensure LM Studio local server is running.", []
        return False, f"LM Studio Connection Error: {err_msg}", []

def generate_streaming_response(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_content: str,
    temperature: float = 0.3
) -> Generator[str, None, None]:
    """
    Streams response text tokens from LM Studio with error handling.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
    except Exception as e:
        err_str = str(e)
        if "context length" in err_str.lower() or "n_keep" in err_str.lower() or "tokens" in err_str.lower():
            yield (
                "\n\n⚠️ **Context Window Exceeded in LM Studio**\n\n"
                f"The document prompt exceeded the model's loaded context window (`{err_str}`).\n\n"
                "**Solutions:**\n"
                "1. In **LM Studio**, reload the model with a larger Context Length (e.g. 16,384 or 32,768 tokens).\n"
                "2. In the app sidebar, reduce **Chunk Size** or enable **Map-Reduce**."
            )
        else:
            yield f"\n\n⚠️ **LM Studio Error**: {err_str}"

def run_single_pass_summary(
    client: OpenAI,
    model: str,
    document_text: str,
    preset_name: str,
    custom_instruction: Optional[str] = None,
    temperature: float = 0.3,
    max_context_chars: int = 12000
) -> Generator[str, None, None]:
    """
    Generates document summary in a single pass for smaller documents.
    """
    system_prompt = PROMPT_PRESETS.get(preset_name, PROMPT_PRESETS["Executive Summary"])
    if custom_instruction and preset_name == "Custom Prompt":
        system_prompt = f"You are a helpful AI assistant. Analyze the document according to these specific instructions:\n{custom_instruction}"
    elif custom_instruction:
        system_prompt += f"\nAdditional Instruction: {custom_instruction}"
        
    # Cap text length to prevent context overflow
    safe_text = document_text[:max_context_chars]
    if len(document_text) > max_context_chars:
        safe_text += "\n\n[... Document truncated for single-pass analysis. Use Map-Reduce for full document analysis ...]"
        
    user_content = f"Here is the document text:\n\n{safe_text}\n\nPlease analyze according to instructions."
    
    return generate_streaming_response(client, model, system_prompt, user_content, temperature)

def map_reduce_summary(
    client: OpenAI,
    model: str,
    chunks: List[Dict[str, Any]],
    preset_name: str,
    custom_instruction: Optional[str] = None,
    temperature: float = 0.3,
    status_callback=None
) -> Generator[str, None, None]:
    """
    Performs Map-Reduce summarization for multi-chunk large PDFs.
    Stage 1: Summarize each chunk into key observations.
    Stage 2: Combine chunk summaries into final formatted report.
    """
    chunk_summaries = []
    total_chunks = len(chunks)
    
    # Map Phase
    for idx, chunk in enumerate(chunks):
        if status_callback:
            status_callback(f"Processing chunk {idx + 1}/{total_chunks} ({chunk['page_range']})...")
            
        map_prompt = (
            "Summarize the following excerpt from a document. Capture all critical facts, data points, "
            "names, and main ideas presented in this section."
        )
        map_user_content = f"Document excerpt ({chunk['page_range']}):\n\n{chunk['text']}"
        
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": map_prompt},
                    {"role": "user", "content": map_user_content}
                ],
                temperature=temperature,
                stream=False
            )
            summary_text = resp.choices[0].message.content or ""
            chunk_summaries.append(f"### Excerpt ({chunk['page_range']}):\n{summary_text}")
        except Exception as e:
            chunk_summaries.append(f"### Excerpt ({chunk['page_range']}):\n(Extraction skipped due to error: {e})")

    if status_callback:
        status_callback("Synthesizing final document summary...")

    combined_map_text = "\n\n".join(chunk_summaries)
    
    # Reduce Phase
    system_prompt = PROMPT_PRESETS.get(preset_name, PROMPT_PRESETS["Executive Summary"])
    if custom_instruction and preset_name == "Custom Prompt":
        system_prompt = f"You are a helpful AI assistant. Synthesize the section summaries into a final report following these instructions:\n{custom_instruction}"
    elif custom_instruction:
        system_prompt += f"\nAdditional Instruction: {custom_instruction}"
        
    user_content = (
        "Below are section-by-section summaries extracted from the full document. "
        "Combine and synthesize them into a coherent, seamless, and high-quality final document report.\n\n"
        f"{combined_map_text}"
    )
    
    return generate_streaming_response(client, model, system_prompt, user_content, temperature)

def chat_stream_response(
    client: OpenAI,
    model: str,
    document_context: str,
    chat_history: List[Dict[str, str]],
    user_question: str,
    temperature: float = 0.3,
    chunks: Optional[List[Dict[str, Any]]] = None,
    max_chat_context_chars: int = 10000
) -> Generator[str, None, None]:
    """
    Grounds chat question in document context and streams response with context length safety.
    """
    # Select context: if chunks provided, score/select top relevant chunks for user question
    selected_context = ""
    if chunks and len(chunks) > 1:
        # Score chunks by keyword matches to question
        q_words = set(w.lower() for w in user_question.split() if len(w) > 3)
        scored_chunks = []
        for c in chunks:
            c_text_lower = c["text"].lower()
            score = sum(1 for w in q_words if w in c_text_lower)
            scored_chunks.append((score, c))
            
        # Sort by relevance score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for score, c in scored_chunks[:3]]
        # Sort top chunks back into document reading order
        top_chunks.sort(key=lambda c: c["chunk_id"])
        
        ctx_parts = [f"--- Section ({c['page_range']}) ---\n{c['text']}" for c in top_chunks]
        selected_context = "\n\n".join(ctx_parts)
    else:
        selected_context = document_context[:max_chat_context_chars]

    system_prompt = (
        "You are an AI Document Assistant. Answer the user's questions accurately based ONLY on the provided PDF content.\n"
        "If the answer cannot be found in the document, explicitly state that the document does not contain that information.\n"
        "Always cite relevant page numbers or section details when possible.\n\n"
        f"--- PDF DOCUMENT CONTENT EXCERPTS ---\n{selected_context}\n--- END DOCUMENT CONTENT ---"
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append recent chat history (up to last 4 messages to save tokens)
    for msg in chat_history[-4:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_question})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
    except Exception as e:
        err_str = str(e)
        if "context length" in err_str.lower() or "n_keep" in err_str.lower() or "tokens" in err_str.lower():
            yield (
                "\n\n⚠️ **Context Window Exceeded**\n\n"
                f"The context sent to LM Studio exceeded the model's context window (`{err_str}`).\n\n"
                "**How to fix:**\n"
                "1. In **LM Studio**, click the model settings and increase **Context Length** (e.g. 16,384 or 32,768 tokens).\n"
                "2. Try asking a more specific question targeting a specific page or section."
            )
        else:
            yield f"\n\n⚠️ **LM Studio Error**: {err_str}"

