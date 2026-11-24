import asyncio
from playwright.async_api import async_playwright

async def test_chrome():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
            headless=True
        )
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"[CHROME CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[CHROME PAGE ERROR] {err}"))
        
        await page.goto("http://localhost:8010/index.html")
        for i in range(10):
            await asyncio.sleep(1)
            sid = await page.evaluate("() => window.sessionid")
            pc_state = await page.evaluate("() => window.pc ? window.pc.connectionState : 'no-pc'")
            ice_state = await page.evaluate("() => window.pc ? window.pc.iceConnectionState : 'no-pc'")
            badge = await page.inner_text("#statusBadge")
            print(f"[{i}s] sid={sid}, pcState={pc_state}, iceState={ice_state}, badge={badge}")
            if sid and pc_state == "connected":
                break
                
        await page.screenshot(path="C:/Users/Tonton Yuta/LiveTalking/tests/chrome_test.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_chrome())
