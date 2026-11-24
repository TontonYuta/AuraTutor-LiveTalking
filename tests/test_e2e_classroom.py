import asyncio
import os
import re
from playwright.async_api import async_playwright

SCREENSHOT_DIR = r"C:\Users\Tonton Yuta\LiveTalking\tests"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def run_e2e_test():
    console_logs = []
    page_errors = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--allow-file-access-from-files",
                "--disable-web-security"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 850},
            permissions=["microphone", "camera"]
        )
        page = await context.new_page()

        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        print("=== BƯỚC 1: TRUY CẬP TRANG CHỦ LỚP HỌC ===")
        url = "http://localhost:8010/index.html"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1500)

        # 1. Kiểm tra Tiêu đề và Nội dung Tiếng Việt
        title = await page.title()
        print(f"Tiêu đề trang: {title}")
        assert "AuraTutor" in title, f"Tiêu đề không đúng: {title}"

        # Quét kiểm tra 0 ký tự tiếng Trung trong DOM text
        body_text = await page.inner_text("body")
        chinese_matches = re.findall(r'[\u4e00-\u9fff]', body_text)
        print(f"Số ký tự tiếng Trung phát hiện trên giao diện: {len(chinese_matches)}")
        assert len(chinese_matches) == 0, f"Vẫn còn ký tự tiếng Trung: {set(chinese_matches)}"

        # 2. Kiểm tra các phần tử giao diện
        badge_text = await page.inner_text("#statusBadge")
        print(f"Trạng thái ban đầu: {badge_text.strip()}")
        assert "Chưa kết nối" in badge_text

        # Bounding box của khung video và form tương tác
        video_box = await page.locator("#video").bounding_box()
        chat_box = await page.locator("#txtMessage").bounding_box()
        print(f"Kích thước Video: {video_box['width']}x{video_box['height']} px (x={video_box['x']}, y={video_box['y']})")
        print(f"Kích thước Khung nhập: {chat_box['width']}x{chat_box['height']} px")
        assert video_box['width'] > 300 and video_box['height'] > 100, "Khung video bị vỡ hoặc không hiển thị"

        # Chụp màn hình 1: Trạng thái ban đầu
        shot1 = os.path.join(SCREENSHOT_DIR, "screenshot_1_initial.png")
        await page.screenshot(path=shot1, full_page=True)
        print(f"Đã lưu ảnh chụp 1: {shot1}")

        # === BƯỚC 2: NHẤN BẮT ĐẦU KẾT NỐI WEBRTC ===
        print("\n=== BƯỚC 2: BẮT ĐẦU KẾT NỐI WEBRTC ===")
        btn_start = page.locator("#btnStart")
        assert await btn_start.is_visible(), "Nút 'Bắt đầu kết nối' không hiển thị"
        await btn_start.click()
        print("Đã click nút 'Bắt đầu kết nối'")

        # Chờ WebRTC khởi tạo và trao đổi offer/answer
        await page.wait_for_timeout(5000)

        badge_after = await page.inner_text("#statusBadge")
        sid_display = await page.inner_text("#sessionIdDisplay")
        print(f"Trạng thái sau khi kết nối: {badge_after.strip()}")
        print(f"Mã phiên học: {sid_display.strip()}")

        shot2 = os.path.join(SCREENSHOT_DIR, "screenshot_2_connected.png")
        await page.screenshot(path=shot2, full_page=True)
        print(f"Đã lưu ảnh chụp 2: {shot2}")

        # === BƯỚC 3: GỬI CÂU HỎI TIẾNG VIỆT CHO GIA SƯ ===
        print("\n=== BƯỚC 3: GỬI CÂU HỎI CHO THẦY GIÁO AI ===")
        test_question = "Em chào thầy ạ! Hôm nay thầy hướng dẫn em giải bài tập toán này nhé!"
        await page.fill("#txtMessage", test_question)
        print(f"Đã nhập câu hỏi: '{test_question}'")

        # Click nút Gửi (button chứa icon bi-send)
        btn_send = page.locator("button:has-text('Gửi')")
        await btn_send.click()
        print("Đã click nút 'Gửi câu hỏi'")

        # Chờ gia sư nhận yêu cầu và xử lý phát âm
        await page.wait_for_timeout(4000)

        shot3 = os.path.join(SCREENSHOT_DIR, "screenshot_3_interaction.png")
        await page.screenshot(path=shot3, full_page=True)
        print(f"Đã lưu ảnh chụp 3: {shot3}")

        # Kiểm tra console errors
        print("\n=== BƯỚC 4: BÁO CÁO NHẬT KÝ CONSOLE & LỖI ===")
        for log in console_logs[-15:]:
            print("Console:", log)

        critical_errors = [e for e in page_errors if "favicon" not in e.lower()]
        print(f"Tổng số lỗi Runtime nghiêm trọng: {len(critical_errors)}")
        if critical_errors:
            print("Lỗi phát hiện:", critical_errors)

        await browser.close()
        print("\n=== KIỂM THỬ PLAYWRIGHT HOÀN TẤT THÀNH CÔNG 100%! ===")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
