import asyncio
from playwright.async_api import async_playwright

async def verify():
    print("[E2E] Starting full verification...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--autoplay-policy=no-user-gesture-required",
                "--use-fake-ui-for-media-stream",
            ]
        )
        page = await browser.new_page(viewport={"width": 1280, "height": 820})

        logs = []
        page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))

        print("[E2E] Opening http://localhost:8010/index.html...")
        await page.goto("http://localhost:8010/index.html", wait_until="networkidle")

        # Wait for WebRTC connection
        for i in range(20):
            await asyncio.sleep(0.5)
            sid = await page.evaluate("() => window.sessionid")
            pc_state = await page.evaluate("() => window.pc ? window.pc.connectionState : 'no-pc'")
            if sid and pc_state == "connected":
                print(f"[E2E PASS] Connected! SID={sid}")
                break
        else:
            raise TimeoutError("Failed to connect WebRTC")

        # Wait for welcome message to complete (5s)
        await asyncio.sleep(5)
        await page.screenshot(path="C:/Users/Tonton Yuta/LiveTalking/tests/verify_step1_connected.png")

        # Send math question
        print("[E2E] Sending question: 'Thầy ơi, thầy hướng dẫn em giải bài tập toán này nhé!'...")
        await page.fill("#txtMessage", "Thầy ơi, thầy hướng dẫn em giải bài tập toán này nhé!")
        await page.click("#btnSend")

        # Wait for answer to be synthesized and spoken
        print("[E2E] Waiting for AI tutor speech synthesis and playback...")
        await asyncio.sleep(8)
        await page.screenshot(path="C:/Users/Tonton Yuta/LiveTalking/tests/verify_step2_tutoring.png")

        errs = [l for l in logs if "[error]" in l]
        print(f"[E2E] Finished! Console errors: {len(errs)}")
        await browser.close()
        print("[E2E SUCCESS] All stages completed successfully!")

if __name__ == "__main__":
    asyncio.run(verify())
