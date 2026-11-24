import asyncio
from playwright.async_api import async_playwright

async def launch_visible_app():
    async with async_playwright() as p:
        # Launch Chromium with UI visible on the user's desktop!
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--app=http://localhost:8010/index.html",
                "--window-size=1200,820",
                "--use-fake-ui-for-media-stream"
            ]
        )
        page = await browser.new_page()
        print("Visible window launched! Keeping it open...")
        # Keep open while user uses it
        while True:
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(launch_visible_app())
