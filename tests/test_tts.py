import asyncio, edge_tts

async def test_both():
    voices = ['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural', 'en-US-GuyNeural']
    texts = [
        'Xin chao',
        'Chào em! Thầy là gia sư AI.',
        'Về câu hỏi môn Toán của em: Thầy ơi, thầy hướng dẫn em giải bài tập toán này nhé!.',
        'Chào em! Thầy là gia sư AI của em hôm nay. Hôm nay em muốn thầy hướng dẫn bài học nào nào?'
    ]
    for v in voices:
        for t in texts:
            try:
                comm = edge_tts.Communicate(t, v)
                data = b''
                async for chunk in comm.stream():
                    if chunk['type'] == 'audio':
                        data += chunk['data']
                print(f"{v} | text='{t[:20]}...' -> SUCCESS ({len(data)} bytes)")
            except Exception as e:
                print(f"{v} | text='{t[:20]}...' -> FAIL: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_both())
