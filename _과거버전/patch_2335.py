# -*- coding: utf-8 -*-
"""2026-09-13 3차 수정 패치: 막대 상향·두껍게, 밀며 치는 물리, 랜덤 번쩍 강타(1.5배)"""
import io, sys, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
p = 'src_index.html'
s = io.open(p, encoding='utf-8').read()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:70])
    s = s.replace(a, b)

# 안내문
rep('<p id="sub" class="rise">화면 맨 아래 띠를 엄지로 좌우로 밀면<br>막대가 따라옵니다 · 먼저 5점을 내면 이깁니다</p>',
    '<p id="sub" class="rise">맨 아래 띠를 엄지로 좌우로 밀면 막대가 따라옵니다<br>옆으로 밀며 치면 공이 세게 나가고,<br>막대가 금빛으로 번쩍일 때 밀며 치면 1.5배 강타<br>먼저 5점을 내면 이깁니다</p>')

# 효과음 2개 추가: 번쩍(충전)·강타
rep("""  function toggle(){""",
"""  function charge(){
    if(!ctx || muted) return;
    const t = ctx.currentTime;
    tone(t, 320, 0.32, 0.22, 'triangle', sfxBus, {bendTo:1280, bendDur:0.28, lp:3000, a:0.01, d:0.2, s:0.5, send:0.5});
    tone(t + 0.26, hz(88), 0.3, 0.2, 'sine', sfxBus, {a:0.004, d:0.1, s:0.3, send:0.6});
  }
  function smash(){
    if(!ctx || muted) return;
    const t = ctx.currentTime;
    tone(t, 150, 0.28, 0.7, 'sine', sfxBus, {bendTo:50, bendDur:0.12, a:0.002, d:0.18, s:0.1});
    noise(t, 0.06, 0.5, 'bandpass', 2200, 0.8, sfxBus);
    tone(t + 0.02, hz(91), 0.22, 0.4, 'triangle', sfxBus, {lp:4000, a:0.003, d:0.1, s:0.1, send:0.5});
  }
  function toggle(){""")
rep("  return {unlock, startMusic, stopMusic, tempo, paddle, wall, won, lost, levelUp, fanfare, toggle, isPlaying};",
    "  return {unlock, startMusic, stopMusic, tempo, paddle, wall, won, lost, levelUp, fanfare, charge, smash, toggle, isPlaying};")

# 상태 변수
rep("  const me  = { x:0, y:0, w:0, h:12 };", "  const me  = { x:0, y:0, w:0, h:12, vx:0, px:0 };   // vx=엄지로 미는 속도(px/s)")
rep("  let smile = 0, smileTarget = 0;              // 0=평소, 1=활짝 웃음",
    "  let smile = 0, smileTarget = 0;              // 0=평소, 1=활짝 웃음\n"
    "  let powerOn = false, powerT = 0, powerCd = 6 + Math.random() * 6;   // 막대 번쩍(강타 기회) 타이머\n"
    "  let pop = null;                              // 강타 글자 {text,x,y,t}\n"
    "  const POWER_LEN = 3;\n"
    "  const UI_FONT = \"'SUIT Variable','SUIT','Pretendard',sans-serif\";")

# 막대 위치·두께
rep("    me.h = cpu.h = Math.max(11, H * 0.016);\n    me.y  = H - H * 0.15 - me.h;              // 엄지보다 위에 두어 손가락에 안 가리게",
    "    cpu.h = Math.max(11, H * 0.016);\n    me.h  = Math.max(18, H * 0.026);           // 내 막대는 두껍게\n    me.y  = H - H * 0.20 - me.h;              // 엄지보다 위에 두어 손가락에 안 가리게")
rep("    const strip = H * 0.105;", "    const strip = H * 0.13;")

# 시작 시 초기화
rep("    faceTarget = FACE_PLAY; smileTarget = 0; smile = 0;\n    resetBall(",
    "    faceTarget = FACE_PLAY; smileTarget = 0; smile = 0;\n    powerOn = false; powerT = 0; powerCd = 6 + Math.random() * 6; pop = null;\n    me.vx = 0; me.px = me.x;\n    resetBall(")

# 물리
rep("""  function bounceOff(p, goingUp){
    const off = clamp((ball.x - p.x) / (p.w / 2), -1, 1);
    const ang = off * MAX_ANGLE;
    ball.mul = Math.min(ball.mul * tun.stepMul, tun.cap);
    const s = ball.speed * ball.mul;
    ball.vx = Math.sin(ang) * s;
    ball.vy = Math.cos(ang) * s * (goingUp ? -1 : 1);
    flash = 1;
    hits++;
    Snd.paddle(hits, level);
    musicTempo();
    if(navigator.vibrate) navigator.vibrate(6);
  }""",
"""  function bounceOff(p, goingUp){
    const off = clamp((ball.x - p.x) / (p.w / 2), -1, 1);
    let ang = off * MAX_ANGLE, power = 1, kind = 0;   // kind 0=보통 1=밀며 침 2=강타
    if(p === me){
      const push = clamp(Math.abs(me.vx) / (W * 2.2), 0, 1);   // 0=멈춘 채 침, 1=빠르게 밀며 침
      if(push > 0.12){
        ang = clamp(ang + Math.sign(me.vx) * push * 0.45, -1.25, 1.25);   // 미는 방향으로 더 꺾임
        power = 1 + 0.35 * push;                                          // 최대 1.35배
        kind = 1;
        if(powerOn){ power = 1.5; kind = 2; powerOn = false; powerCd = 6 + Math.random() * 6; }
      }
    }
    ball.mul = Math.min(ball.mul * tun.stepMul, tun.cap);
    const s = ball.speed * ball.mul * power;           // power는 이번 한 번의 반발에만 적용
    ball.vx = Math.sin(ang) * s;
    ball.vy = Math.cos(ang) * s * (goingUp ? -1 : 1);
    flash = kind === 2 ? 1.6 : (kind === 1 ? 1 + (power - 1) : 1);
    hits++;
    if(kind === 2){
      Snd.smash();
      pop = {text:'강타 ×1.5', x:ball.x, y:me.y - 26, t:1.0};
      if(navigator.vibrate) navigator.vibrate([14, 24, 14]);
    }else{
      Snd.paddle(hits, level);
      if(navigator.vibrate) navigator.vibrate(kind === 1 ? 9 : 6);
    }
    musicTempo();
  }""")

# update
rep("""    if(state !== 'play') return;

    playTime += dt;
    updateLevel();
""",
"""    if(state !== 'play') return;

    playTime += dt;
    updateLevel();

    // 내 막대 속도(엄지로 미는 빠르기) — 살짝 평활
    me.vx = me.vx * 0.45 + ((me.x - me.px) / dt) * 0.55;
    me.px = me.x;

    // 랜덤 번쩍: 6~12초마다 3초 동안 막대가 금빛으로 빛남
    if(powerOn){
      powerT -= dt;
      if(powerT <= 0){ powerOn = false; powerCd = 6 + Math.random() * 6; }
    }else{
      powerCd -= dt;
      if(powerCd <= 0){ powerOn = true; powerT = POWER_LEN; Snd.charge(); if(navigator.vibrate) navigator.vibrate(20); }
    }
    if(pop){ pop.t -= dt; pop.y -= dt * 40; if(pop.t <= 0) pop = null; }
""")
rep("""    if(state === 'serve'){
      serveTimer -= dt;
      if(serveTimer <= 0) state = 'play';
      return;
    }""",
"""    if(state === 'serve'){
      serveTimer -= dt;
      me.vx = 0; me.px = me.x;
      if(serveTimer <= 0) state = 'play';
      return;
    }""")

# 그리기
rep("""  function pill(x, y, w, h, color, glow){
    ctx.save();
    ctx.shadowColor = glow; ctx.shadowBlur = 16; ctx.shadowOffsetY = 6;""",
"""  function pill(x, y, w, h, color, glow, blur){
    ctx.save();
    ctx.shadowColor = glow; ctx.shadowBlur = blur || 16; ctx.shadowOffsetY = 6;""")
rep("""    pill(me.x - me.w / 2, me.y, me.w, me.h, '#2F6BFF', 'rgba(47,107,255,.35)');""",
"""    if(powerOn){
      const pulse = 0.5 + 0.5 * Math.sin(performance.now() / 70);          // 번쩍임
      pill(me.x - me.w / 2, me.y, me.w, me.h, pulse > 0.5 ? '#FFC93C' : '#F5A800', 'rgba(255,190,40,' + (0.55 + 0.4 * pulse) + ')', 26 + 18 * pulse);
      // 남은 시간 고리
      ctx.strokeStyle = 'rgba(245,168,0,.9)'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(me.x, me.y - 16, 8, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (powerT / POWER_LEN)); ctx.stroke();
    }else{
      pill(me.x - me.w / 2, me.y, me.w, me.h, '#2F6BFF', 'rgba(47,107,255,.35)');
    }""")
rep("""    // 타격 잔광
    if(flash > 0){
      ctx.fillStyle = 'rgba(255,255,255,' + (flash * 0.9) + ')';
      ctx.beginPath(); ctx.arc(ball.x, ball.y, ball.r + 12 * flash, 0, Math.PI * 2); ctx.fill();
    }""",
"""    // 타격 잔광
    if(flash > 0){
      ctx.fillStyle = 'rgba(255,255,255,' + Math.min(1, flash * 0.9) + ')';
      ctx.beginPath(); ctx.arc(ball.x, ball.y, ball.r + 12 * flash, 0, Math.PI * 2); ctx.fill();
    }
    // 강타 글자
    if(pop){
      ctx.save();
      ctx.globalAlpha = Math.min(1, pop.t * 2);
      ctx.font = '800 22px ' + UI_FONT;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineWidth = 6; ctx.strokeStyle = 'rgba(244,242,238,.9)'; ctx.strokeText(pop.text, pop.x, pop.y);
      ctx.fillStyle = '#C27A00'; ctx.fillText(pop.text, pop.x, pop.y);
      ctx.restore();
    }""")
# 검증창
rep("    get faceA(){ return faceA; }, get tuning(){ return tun; },",
    "    get faceA(){ return faceA; }, get tuning(){ return tun; },\n"
    "    get powerOn(){ return powerOn; }, get powerT(){ return powerT; }, get pop(){ return pop; },\n"
    "    setPower: function(on){ powerOn = on; powerT = on ? POWER_LEN : 0; },")

io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patch ok')
