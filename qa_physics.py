# -*- coding: utf-8 -*-
"""검증용: 멈춘 채 치기 / 밀며 치기 / 번쩍 강타 세 경우의 반발 속도를 비교하고, 랜덤 번쩍이 실제로 켜지는지 본다.
사용: python qa_physics.py <출력폴더> [파일 또는 URL]
"""
import asyncio, sys, os, json, math
from playwright.async_api import async_playwright

OUT = sys.argv[1]
TARGET = sys.argv[2] if len(sys.argv) > 2 else 'file:///' + os.path.abspath('index.html').replace(chr(92), '/')
os.makedirs(OUT, exist_ok=True)

HIT_JS = """(step) => new Promise(res => {
  const pp = window.__pp, me = pp.me, ball = pp.ball;
  // 공을 막대 바로 위에 놓고 아래로 떨어뜨린다(서브 상태면 play로 넘어갈 때까지 기다림)
  const start = () => {
    me.x = pp.size().W / 2 - (step > 0 ? 80 : 0); me.px = me.x; me.vx = 0;
    ball.x = me.x + (step > 0 ? 60 : 0); ball.y = me.y - 70; ball.vx = 0; ball.vy = 700; ball.mul = 1;
    let n = 0;
    const prevHits = pp.hits;
    const loop = () => {
      me.x += step; n++;
      if(pp.hits > prevHits || n > 60){
        res({hit: pp.hits > prevHits, vx: ball.vx, vy: ball.vy, speed: Math.hypot(ball.vx, ball.vy), base: ball.speed, mul: ball.mul,
             mevx: me.vx, pop: pp.pop ? pp.pop.text : null, powerOn: pp.powerOn, n});
      } else requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  };
  const wait = () => { if(pp.state === 'play') start(); else setTimeout(wait, 50); };
  wait();
})"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True)
        errors = []
        pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
        await pg.goto(TARGET)
        await pg.wait_for_timeout(1200)
        await pg.click('#action')
        await pg.wait_for_timeout(1000)
        geo = await pg.evaluate("({meY:__pp.me.y, meH:__pp.me.h, H:__pp.size().H, cpuH:__pp.cpu.h})")

        still = await pg.evaluate(HIT_JS, 0)
        await pg.wait_for_timeout(300)
        moving = await pg.evaluate(HIT_JS, 13)
        await pg.wait_for_timeout(300)
        await pg.evaluate("__pp.setPower(true)")
        await pg.wait_for_timeout(120)
        await pg.screenshot(path=f'{OUT}/power_on.png')
        power = await pg.evaluate(HIT_JS, 13)
        await pg.wait_for_timeout(80)
        await pg.screenshot(path=f'{OUT}/smash.png')
        await pg.evaluate("__pp.setPower(true)")
        await pg.wait_for_timeout(120)
        power_still = await pg.evaluate(HIT_JS, 0)   # 번쩍이지만 멈춘 채 치면 보통

        # 랜덤 번쩍이 자연히 켜지는지(최대 20초 관찰)
        seen = None; t0 = 0
        for i in range(400):
            st = await pg.evaluate("({on:__pp.powerOn, t:__pp.powerT, s:__pp.state, bx:__pp.ball.x, pt:__pp.playTime})")
            if st['s'] == 'over': break
            await pg.mouse.move(st['bx'], 700)
            if st['on'] and seen is None: seen = st['pt']
            if seen is not None and not st['on']: t0 = st['pt']; break
            await pg.wait_for_timeout(50)

        def ratio(a, b): return round(a['speed'] / b['speed'], 3) if b['speed'] else None
        print(json.dumps({
            'geometry': geo,
            'still': still, 'moving': moving, 'power_moving': power, 'power_still': power_still,
            'ratio_moving_vs_still': ratio(moving, still),
            'ratio_power_vs_still': ratio(power, still),
            'ratio_powerstill_vs_still': ratio(power_still, still),
            'random_flash': {'first_on_at_playTime': seen, 'off_at_playTime': t0, 'duration': (round(t0 - seen, 2) if seen and t0 else None)},
            'errors': errors}, ensure_ascii=False, indent=1))
        await b.close()

asyncio.run(main())
