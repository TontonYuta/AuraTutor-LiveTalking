import asyncio
from playwright.async_api import async_playwright

async def test_browser(browser_type_name):
    print(f"\n--- Testing with {browser_type_name} ---")
    async with async_playwright() as p:
        b_type = getattr(p, browser_type_name)
        try:
            browser = await b_type.launch(headless=True)
        except Exception as e:
            print(f"Could not launch {browser_type_name}: {e}")
            return
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"[{browser_type_name} CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[{browser_type_name} PAGE ERROR] {err}"))
        page.on("requestfailed", lambda req: print(f"[{browser_type_name} REQ FAILED] {req.url} - {req.failure}"))
        
        try:
            resp = await page.goto("http://localhost:8010/index.html", timeout=10000)
            print(f"Status: {resp.status}")
        except Exception as e:
            print(f"Goto error: {e}")
            await browser.close()
            return
            
        await asyncio.sleep(4)
        sid = await page.evaluate("() => window.sessionid")
        pc_state = await page.evaluate("() => window.pc ? window.pc.connectionState : 'no-pc'")
        ice_state = await page.evaluate("() => window.pc ? window.pc.iceConnectionState : 'no-pc'")
        badge = await page.inner_text("#statusBadge")
        error_display = await page.inner_text("#offerError")
        print(f"Result -> sessionid: {sid}, pc.connectionState: {pc_state}, iceConnectionState: {ice_state}, badge: {badge}")
        if error_display:
            print(f"Offer error: {error_display}")
            
        # Try sending a text message
        print("Testing sendText()...")
        await page.fill("#txtMessage", "Thầy ơi em chào thầy!")
        await page.click("button:has-text('Gửi câu hỏi')")
        await asyncio.sleep(2)
        await page.screenshot(path=f"C:/Users/Tonton Yuta/LiveTalking/tests/debug_{browser_type_name}.png")
        await browser.close()

async def main():
    await test_browser("chromium")
    await test_browser("firefox")

if __name__ == "__main__":
    asyncio.run(main())
