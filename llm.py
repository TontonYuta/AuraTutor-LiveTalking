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
    """Tạo câu trả lời sư phạm tiếng Việt thông minh, trực diện khi không có API key ngoài."""
    msg = (message or "").lower().strip()

    # 1. Tự động tính toán các phép toán số học trực tiếp
    arithmetic_match = re.search(r'(\d+(?:\.\d+)?)\s*([\+\-\*\/xX÷cộngtrừnhânchia])\s*(\d+(?:\.\d+)?)', msg)
    if arithmetic_match:
        try:
            num1 = float(arithmetic_match.group(1))
            op_raw = arithmetic_match.group(2)
            num2 = float(arithmetic_match.group(3))
            if op_raw in ['+', 'cộng']:
                res = num1 + num2
                op_name = "cộng"
            elif op_raw in ['-', 'trừ']:
                res = num1 - num2
                op_name = "trừ"
            elif op_raw in ['*', 'x', 'X', 'nhân']:
                res = num1 * num2
                op_name = "nhân"
            elif op_raw in ['/', '÷', 'chia']:
                res = num1 / num2 if num2 != 0 else "vô cực (không thể chia cho 0)"
                op_name = "chia"
            else:
                res = None
            if res is not None:
                res_str = f"{res:.2f}".rstrip('0').rstrip('.') if isinstance(res, float) else str(res)
                n1_str = f"{num1:.2f}".rstrip('0').rstrip('.')
                n2_str = f"{num2:.2f}".rstrip('0').rstrip('.')
                return f"Kết quả phép tính của em là: {n1_str} {op_name} {n2_str} bằng {res_str}. Em làm rất tốt, hãy cùng thầy tiếp tục làm thêm các bài toán khác nhé!"
        except Exception:
            pass

    # 2. Cơ sở tri thức giải đáp trực diện các câu hỏi khoa học, tự nhiên & xã hội
    if "thủ đô" in msg and ("việt nam" in msg or "nước ta" in msg or "vn" in msg):
        return "Thủ đô của nước Cộng hòa Xã hội Chủ nghĩa Việt Nam là thành phố Hà Nội, trung tâm đầu não chính trị, kinh tế và văn hóa lâu đời của đất nước ta em nhé."
    elif any(k in msg for k in ["lá cây", "diệp lục", "màu xanh của lá"]):
        return "Lá cây có màu xanh là nhờ chất diệp lục (chlorophyll) trong lục lạp. Phân tử diệp lục hấp thụ mạnh ánh sáng đỏ và xanh lam từ mặt trời để quang hợp, nhưng phản xạ lại ánh sáng xanh lục đến mắt chúng ta, làm cho lá có màu xanh."
    elif "quang hợp" in msg:
        return "Quang hợp là quá trình thực vật sử dụng năng lượng ánh sáng mặt trời được diệp lục hấp thụ để tổng hợp chất hữu cơ (glucose) và giải phóng khí oxy từ nước và khí carbon dioxide."
    elif any(k in msg for k in ["newton", "vạn vật hấp dẫn"]):
        return "Định luật vạn vật hấp dẫn của Isaac Newton phát biểu: Mọi vật thể trong vũ trụ đều hút nhau với một lực tỉ lệ thuận với tích khối lượng của chúng và tỉ lệ nghịch với bình phương khoảng cách giữa chúng, theo công thức F bằng G nhân m1 nhân m2 chia cho r bình phương."
    elif any(k in msg for k in ["định luật ôm", "định luật ohm"]):
        return "Định luật Ôm trong vật lý phát biểu: Cường độ dòng điện chạy qua một dây dẫn tỉ lệ thuận với hiệu điện thế giữa hai đầu dây và tỉ lệ nghịch với điện trở của dây đó. Công thức là I bằng U chia cho R."
    elif any(k in msg for k in ["pythagore", "pi-ta-go", "pitago"]):
        return "Định lý Pythagore trong tam giác vuông phát biểu: Bình phương độ dài cạnh huyền bằng tổng bình phương độ dài hai cạnh góc vuông, công thức là a bình phương cộng b bình phương bằng c bình phương."
    elif any(k in msg for k in ["diện tích hình tròn", "hình tròn"]):
        return "Công thức tính diện tích hình tròn là S bằng số Pi nhân với bán kính bình phương (S = π * r^2). Chu vi hình tròn là C bằng 2 nhân Pi nhân bán kính em nhé."
    elif "mặt trăng" in msg and any(k in msg for k in ["đầu tiên", "ai", "đặt chân"]):
        return "Con người đầu tiên đặt chân lên Mặt Trăng là nhà du hành vũ trụ người Mỹ Neil Armstrong vào ngày 20 tháng 7 năm 1969, trong sứ mệnh lịch sử Apollo 11 của cơ quan NASA."
    elif "nước sôi" in msg or "đóng băng" in msg:
        return "Ở áp suất khí quyển tiêu chuẩn 1 atm, nước tinh khiết sôi và chuyển thành hơi ở 100 độ C, và đóng băng thành thể rắn ở 0 độ C em nhé."
    elif any(k in msg for k in ["mẹo", "phương pháp", "bí quyết", "hiệu quả"]):
        return "Để học tập đạt hiệu quả cao nhất, em nên áp dụng kỹ thuật Pomodoro học tập ngắt quãng 25 phút, kết hợp sơ đồ tư duy Mindmap và thực hành giải bài tập ngay sau khi học lý thuyết em nhé!"
    elif any(k in msg for k in ["chào", "hello", "hi", "thầy ơi", "alo", "bắt đầu"]):
        return "Chào em! Thầy là gia sư AI của em hôm nay. Thầy rất vui được đồng hành cùng em trong tiết học 1 kèm 1 này. Em có câu hỏi hay bài tập nào cần thầy hướng dẫn ngay không nào?"
    elif any(k in msg for k in ["lập trình", "python", "code", "ai", "webrtc"]):
        return f"Về chủ đề công nghệ: '{message}'. Đây là một kiến trúc rất thú vị. Trong lập trình, em nên chia nhỏ bài toán thành các hàm độc lập, kiểm thử kỹ từng module để chương trình vận hành mượt mà nhất nhé!"
    else:
        return f"Về câu hỏi: '{message}'. Để thầy có thể phân tích sâu và giải chi tiết từng bước cho mọi bài tập nâng cao của em, em hãy dán API Key (như Gemini miễn phí) vào ô 'Trí Tuệ Nhân Tạo' ở cột bên phải nhé!"


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
