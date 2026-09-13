# -*- coding: utf-8 -*-
"""검증용: 데스크톱·가로·작은 폰 화면에서 시작/플레이/승리 화면을 캡처한다.
사용: python qa_shots.py <출력폴더> [파일 또는 URL]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright

OUT = sys.argv[1]
TARGET = sys.argv[2] if len(sys.argv) > 2 else 'file:///' + os.path.abspath('index.html').replace(chr(92), '/')
os.makedirs(OUT, exist_ok=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, vw, vh, dsf in [('desktop', 1280, 800, 1), ('landscape', 844, 390, 2), ('small', 360, 740, 2)]:
            pg = await b.new_page(viewport={'width': vw, 'height': vh}, device_scale_factor=dsf)
            await pg.goto(TARGET)
            await pg.wait_for_timeout(1600)
            await pg.screenshot(path=f'{OUT}/{name}_intro.png')
            await pg.click('#action')
            await pg.wait_for_timeout(1500)
            await pg.screenshot(path=f'{OUT}/{name}_play.png')
            # 승리 화면 강제(말풍선 위치 확인): 내 점수 4점으로 두고 공을 위로 내보낸다
            await pg.evaluate("__pp.score.me = 4")
            for i in range(80):
                await pg.evaluate("(function(){ __pp.ball.y = -100; __pp.ball.vy = -1; })()")
                await pg.wait_for_timeout(30)
                if await pg.evaluate("__pp.state") == 'over':
                    break
            await pg.wait_for_timeout(900)
            await pg.screenshot(path=f'{OUT}/{name}_win.png')
            print(name, await pg.evaluate("__pp.state"), await pg.evaluate("document.getElementById('headline').textContent"))
            await pg.close()
        await b.close()

asyncio.run(main())
