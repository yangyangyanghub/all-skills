"""仅保存登录态，不录制视频"""
import asyncio, json, time
from playwright.async_api import async_playwright

async def main():
  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    await page.goto("http://localhost:5173/", wait_until="domcontentloaded", timeout=30000)
    print(f"打开浏览器: {page.url}")
    print("请在浏览器中登录，脚本会自动检测登录完成...")
    start = time.time()
    while time.time() - start < 300:
      if "/login" not in page.url.lower():
        await page.wait_for_timeout(2000)
        await context.storage_state(path="hf_project/login-state.json")
        elapsed = int(time.time() - start)
        print(f"登录完成（{elapsed}s），登录态已保存")
        break
      await page.wait_for_timeout(1000)
    else:
      print("超时未登录")
    await context.close()
    await browser.close()

asyncio.run(main())