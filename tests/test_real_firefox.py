import asyncio
from playwright.async_api import async_playwright

async def test_real_firefox():
    print("Testing with real Firefox...")
    async with async_playwright() as p:
        try:
            browser = await p.firefox.launch(
                executable_path="C:/Program Files/Mozilla Firefox/firefox.exe",
                headless=True
            )
        except Exception as e:
            print(f"Failed to launch Firefox directly: {e}")
            return
            
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"[FIREFOX CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[FIREFOX PAGE ERROR] {err}"))
        
        await page.goto("http://localhost:8010/index.html")
        await asyncio.sleep(5)
        
        sid = await page.evaluate("() => window.sessionid")
        pc_state = await page.evaluate("() => window.pc ? window.pc.connectionState : 'no-pc'")
        ice_state = await page.evaluate("() => window.pc ? window.pc.iceConnectionState : 'no-pc'")
        badge = await page.inner_text("#statusBadge")
        err = await page.inner_text("#offerError")
        print(f"FIREFOX: sid={sid}, pcState={pc_state}, iceState={ice_state}, badge={badge}, err={err}")
        await page.screenshot(path="C:/Users/Tonton Yuta/LiveTalking/tests/debug_real_firefox.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_firefox())
