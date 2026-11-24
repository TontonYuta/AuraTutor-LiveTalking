import time
import os
import re
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from avatars.base_avatar import BaseAvatar
from utils.logger import logger

# Built-in LLM providers. Each exposes an OpenAI-compatible chat completions
# endpoint; the active one is selected with --llm_provider (default: dashscope).
LLM_PROVIDERS = {
    "groq": {
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "api_key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.0-flash",
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "default_model": "gpt-4o-mini",
    },
    "ollama": {
        "api_key_env": "OLLAMA_API_KEY",
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5:latest",
    },
    "dashscope": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
    },
    "orcarouter": {
        "api_key_env": "ORCAROUTER_API_KEY",
        "base_url": "https://api.orcarouter.ai/v1",
        "default_model": "orcarouter/auto",
    },
}


def _llm_provider(opt) -> str:
    """Tự động phát hiện nhà cung cấp LLM tốt nhất dựa trên API key có sẵn trong môi trường."""
    configured = getattr(opt, 'llm_provider', None)
    if configured and configured in LLM_PROVIDERS and os.getenv(LLM_PROVIDERS[configured]['api_key_env']):
        return configured

    # Tự động ưu tiên Groq (siêu tốc ~0.15s) -> Gemini (~0.4s miễn phí) -> DeepSeek -> OpenAI
    for p in ["groq", "gemini", "deepseek", "openai", "dashscope", "ollama"]:
        key_env = LLM_PROVIDERS[p]['api_key_env']
        if os.getenv(key_env):
            return p

    return configured or 'openai'


def _llm_client(opt):
    """Create the OpenAI-compatible client for the configured provider."""
    from openai import OpenAI
    cfg = LLM_PROVIDERS.get(_llm_provider(opt), LLM_PROVIDERS['dashscope'])
    return OpenAI(
        api_key=os.getenv(cfg['api_key_env']),
        base_url=cfg['base_url'],
    )


def _llm_model(opt) -> str:
    """Resolve the model name, falling back to the provider default."""
    cfg = LLM_PROVIDERS.get(_llm_provider(opt), LLM_PROVIDERS['dashscope'])
    return getattr(opt, 'llm_model', '') or cfg['default_model']


def _generate_smart_tutor_response(message: str) -> str:
    """Tạo câu trả lời sư phạm tiếng Việt thông minh khi không có API key ngoài."""
    msg = (message or "").lower().strip()
    if any(k in msg for k in ["toán", "đạo hàm", "tích phân", "hình học", "phương trình", "đại số", "hình"]):
        return f"Về câu hỏi môn Toán của em: '{message}'. Phương pháp tối ưu cho dạng bài này là em cần xác định rõ điều kiện bài toán, áp dụng công thức nền tảng và chia nhỏ từng bước tính toán. Thầy và em cùng phân tích chi tiết nhé!"
    elif any(k in msg for k in ["lập trình", "python", "code", "ai", "deepfake", "webrtc", "máy tính"]):
        return f"Về chủ đề công nghệ và lập trình này: '{message}'. Đây là một bài toán rất hấp dẫn trong Computer Vision và AI thời gian thực. Em cần chú ý tối ưu hóa luồng xử lý và đồng bộ khung hình để đạt hiệu năng cao nhất nhé!"
    elif any(k in msg for k in ["tiếng anh", "english", "ngữ pháp", "từ vựng", "phát âm"]):
        return f"Đối với môn Tiếng Anh: '{message}'. Việc luyện phản xạ và phát âm chuẩn tự nhiên theo từng ngữ cảnh là quan trọng nhất. Thầy sẽ cùng em luyện tập để nâng cao sự tự tin nhé!"
    elif any(k in msg for k in ["newton", "vật lý", "vận tốc", "gia tốc", "hấp dẫn", "lực"]):
        return f"Về câu hỏi Vật lý của em: '{message}'. Định luật này mô tả sự tương tác cơ bản của tự nhiên. Em hãy chú ý đến các đại lượng vật lý và đơn vị đo chuẩn nhé!"
    elif any(k in msg for k in ["mẹo", "phương pháp", "bí quyết", "hiệu quả"]):
        return "Để học tập đạt hiệu quả cao nhất, em nên áp dụng kỹ thuật Pomodoro học tập ngắt quãng 25 phút, kết hợp ghi chú sơ đồ tư duy và thực hành giải bài tập ngay sau khi học lý thuyết em nhé!"
    elif any(k in msg for k in ["chào", "hello", "hi", "thầy ơi", "alo", "bắt đầu"]):
        return "Chào em! Thầy là gia sư AI của em hôm nay. Thầy rất vui được đồng hành cùng em trong tiết học 1 kèm 1 này. Em có câu hỏi hay bài tập nào cần thầy hướng dẫn ngay không nào?"
    else:
        return f"Thầy đã lắng nghe câu hỏi của em: '{message}'. Đây là một thắc mắc rất hay trong bài học hôm nay! Thầy đang cùng em phân tích và tìm ra lời giải chính xác nhất nhé."


def llm_response(message,avatar_session:'BaseAvatar',datainfo:dict={}):
    try:
        opt = avatar_session.opt
        provider = _llm_provider(opt)
        cfg = LLM_PROVIDERS.get(provider, LLM_PROVIDERS['dashscope'])
        api_key = os.getenv(cfg['api_key_env'])
        
        # Nếu chưa cấu hình API key, tự động kích hoạt bộ gia sư sư phạm thông minh
        if not api_key:
            logger.info(f"LLM API key not set for {provider} ({cfg['api_key_env']}), using built-in smart tutor fallback.")
            reply = _generate_smart_tutor_response(message)
            clean = re.sub(r'[\'"`]', '', reply)
            sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if re.search(r'[\w\d]', s)]
            for s in sentences:
                avatar_session.put_msg_txt(s, datainfo)
            return

        start = time.perf_counter()
        client = _llm_client(opt)
        model = _llm_model(opt)
        end = time.perf_counter()
        logger.info(f"llm Time init: {end-start}s,{message}")
        completion = client.chat.completions.create(
            model=model,
            messages=[{'role': 'system', 'content': 'Bạn là thầy giáo/gia sư trực tuyến 1:1 người Việt Nam thân thiện, nhiệt tình. Hãy trả lời học sinh bằng tiếng Việt ngắn gọn, dễ hiểu, giàu tính sư phạm theo phong cách đàm thoại trực tiếp.'},
                    {'role': 'user', 'content': message}],
            stream=True,
            # Display token usage in the last line of the streamed response.
            stream_options={"include_usage": True}
        )
        result=""
        first = True
        for chunk in completion:
            if len(chunk.choices)>0:
                if first:
                    end = time.perf_counter()
                    logger.info(f"llm Time to first chunk: {end-start}s")
                    first = False
                msg = chunk.choices[0].delta.content
                if msg is None:
                    continue
                lastpos=0
                for i, char in enumerate(msg):
                    if char in ",.!;:，。！？：；" :
                        result = result+msg[lastpos:i+1]
                        lastpos = i+1
                        if len(result)>10:
                            logger.info(result)
                            avatar_session.put_msg_txt(result,datainfo)
                            result=""
                result = result+msg[lastpos:]
        end = time.perf_counter()
        logger.info(f"llm Time to last chunk: {end-start}s")
        if result:
            avatar_session.put_msg_txt(result,datainfo)

    except Exception as e:
        logger.warning(f"llm error ({e}), switching to built-in smart tutor fallback.")
        fallback = _generate_smart_tutor_response(message)
        clean = re.sub(r'[\'"`]', '', fallback)
        sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if re.search(r'[\w\d]', s)]
        for s in sentences:
            avatar_session.put_msg_txt(s, datainfo)
