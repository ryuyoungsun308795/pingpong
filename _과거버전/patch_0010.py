# -*- coding: utf-8 -*-
"""2026-09-14 4차 패치: 내 막대 폭 = 제아와 동일(레벨 축소 제거), 아래 띠에 엄지 손잡이·안내 표시"""
import io, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
p = 'src_index.html'
s = io.open(p, encoding='utf-8').read()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:70])
    s = s.replace(a, b)

# 1) 막대 폭 축소 제거 — 내 막대와 제아 막대 폭 항상 동일
rep("      padScale: Math.max(0.72, 1 - 0.035 * k)    // 내 막대 폭 배율",
    "      padScale: 1                                // 내 막대 폭 = 제아와 동일(레벨과 무관)")

# 2) 아래 띠: 안내 글·트랙·엄지 손잡이(막대 x를 따라감)·막대와 잇는 점선
rep("""    ctx.strokeStyle = 'rgba(20,24,31,.10)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, H - strip + 0.5); ctx.lineTo(W, H - strip + 0.5); ctx.stroke();""",
"""    ctx.strokeStyle = 'rgba(20,24,31,.12)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, H - strip + 0.5); ctx.lineTo(W, H - strip + 0.5); ctx.stroke();
    // 띠 안: 안내 글 + 트랙 + 엄지 손잡이(막대와 같은 x) + 막대까지 점선
    const ty = H - strip * 0.42;
    ctx.font = '700 13px ' + UI_FONT; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(20,24,31,.45)';
    ctx.fillText('◂  엄지로 좌우로 밀기  ▸', W / 2, H - strip + 18);
    ctx.strokeStyle = 'rgba(20,24,31,.14)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(22, ty); ctx.lineTo(W - 22, ty); ctx.stroke();
    ctx.setLineDash([3, 6]); ctx.strokeStyle = 'rgba(47,107,255,.45)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(me.x, ty - 14); ctx.lineTo(me.x, me.y + me.h + 4); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(47,107,255,.22)';
    ctx.beginPath(); ctx.arc(me.x, ty, 20, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#2F6BFF';
    ctx.beginPath(); ctx.arc(me.x, ty, 11, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.9)';
    ctx.beginPath(); ctx.arc(me.x, ty, 4, 0, Math.PI * 2); ctx.fill();""")

io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patch ok')
