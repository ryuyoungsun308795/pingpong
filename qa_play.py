# -*- coding: utf-8 -*-
"""검증용: 게임을 휴대폰 크기로 열어 자동으로 한 판 치르고 화면을 캡처한다.
사용: python qa_play.py <출력폴더> [win|lose] [파일 또는 URL]
"""
import asyncio, sys, os, json
from playwright.async_api import async_playwright

OUT = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else 'win'
TARGET = sys.argv[3] if len(sys.argv) > 3 else 'file:///' + os.path.abspath('index.html').replace('\\', '/')
os.makedirs(OUT, exist_ok=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True)
        errors = []
        pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
        await pg.goto(TARGET)
        await pg.wait_for_timeout(1800)
        await pg.screenshot(path=f'{OUT}/01_intro.png')
        fonts = await pg.evaluate("[document.fonts.check(\"16px 'SUIT Variable'\"), document.fonts.check(\"italic 700 16px Fraunces\")]")
        await pg.click('#action')
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=f'{OUT}/02_serve.png')

        # 자동 플레이: win이면 공을 완벽히 따라가고, lose면 가만히 둔다
        snaps = {}
        for i in range(2400):   # 최대 약 120초
            st = await pg.evaluate("({s:__pp.state, lv:__pp.level, me:__pp.score.me, cpu:__pp.score.cpu, bx:__pp.ball.x, by:__pp.ball.y, hits:__pp.hits, t:__pp.playTime, mul:__pp.ball.mul, mw:__pp.me.w, tun:__pp.tuning})")
            if st['s'] == 'over':
                break
            if MODE == 'win':
                await pg.mouse.move(st['bx'], 760)
            lv = st['lv']
            if lv not in snaps:
                snaps[lv] = {'t': round(st['t'], 1), 'hits': st['hits'], 'me_w': round(st['mw'], 1), 'cpuChase': st['tun']['cpuChase'], 'base': st['tun']['base']}
                if lv in (2, 4):
                    await pg.screenshot(path=f'{OUT}/03_level{lv}.png')
            await pg.wait_for_timeout(40)
        await pg.wait_for_timeout(900)
        final = await pg.evaluate("({s:__pp.state, lv:__pp.level, me:__pp.score.me, cpu:__pp.score.cpu, faceA:__pp.faceA, bubble:!document.getElementById('bubble').hidden, headline:document.getElementById('headline').textContent, detail:document.getElementById('detail').textContent, bubbleBox:(function(){const b=document.getElementById('bubble');const r=b.getBoundingClientRect();return [r.left,r.top,r.width,r.height]})(), face:__pp.faceRect()})")
        await pg.screenshot(path=f'{OUT}/04_over_{MODE}.png')
        # 다시 하기 → 초기화 확인
        await pg.click('#action')
        await pg.wait_for_timeout(300)
        again = await pg.evaluate("({s:__pp.state, lv:__pp.level, me:__pp.score.me, cpu:__pp.score.cpu, bubble:!document.getElementById('bubble').hidden})")
        print(json.dumps({'fonts': fonts, 'levels': snaps, 'final': final, 'restart': again, 'errors': errors}, ensure_ascii=False, indent=1))
        await b.close()

asyncio.run(main())
