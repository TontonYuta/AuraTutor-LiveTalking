import re

reply = "Về câu hỏi môn Toán của em: 'Thầy ơi, thầy hướng dẫn em giải bài tập toán này nhé!'. Phương pháp tối ưu cho dạng bài này là em cần xác định rõ điều kiện bài toán, áp dụng công thức nền tảng và chia nhỏ từng bước tính toán. Thầy và em cùng phân tích chi tiết nhé!"
clean = re.sub(r'[\'"`]', '', reply)
sentences = [s.strip() for s in re.split(r'[.!?]+', clean) if re.search(r'[\w\d]', s)]
print('Clean sentences:')
for i, s in enumerate(sentences):
    print(f"{i}: {repr(s)}")
