import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D

FP = fm.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
FP_B = fm.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

C_WARM = (0.91, 0.36, 0.18)
C_MID  = (0.62, 0.55, 0.42)
C_COLD = (0.22, 0.38, 0.62)
C_GOLD = (0.78, 0.63, 0.24)

def m_color(t):
    t = max(-1, min(1, t))
    if t < 0:
        k = t + 1
        return tuple(C_COLD[i]*(1-k) + C_MID[i]*k for i in range(3))
    else:
        return tuple(C_MID[i]*(1-t) + C_WARM[i]*t for i in range(3))

def m_china(t):
    if t < 0.15: return 0.2 + 0.2*np.sin(t*25)
    if t < 0.35: return -0.2 - 0.35*((t-0.15)/0.2)
    if t < 0.62: return 0.75 - 0.15*((t-0.35)/0.27)
    if t < 0.85: return 0.3 - 0.6*((t-0.62)/0.23)
    return -0.35 + 0.15*np.sin(t*25)

def m_west(t):
    if t < 0.3: return -0.4 + 0.15*np.sin(t*18)
    if t < 0.6: return 0.2 + 0.3*((t-0.3)/0.3)
    if t < 0.82: return 0.5 - 0.35*((t-0.6)/0.22)
    return -0.2 - 0.25*((t-0.82)/0.18)

def m_south(t):
    if t < 0.4: return -0.5 + 0.1*np.sin(t*12)
    if t < 0.62: return 0.35 + 0.2*np.sin((t-0.4)*14)
    return -0.1 - 0.3*((t-0.62)/0.38)

def m_possible(t):
    if t < 0.68: return m_china(t)*0.75
    return -0.35 + 1.0*((t-0.68)/0.32)*(0.7+0.3*np.sin(t*10))

def gen_helix(turns, r, m_func, seed, n=800):
    t = np.linspace(0, 1, n)
    ang = t * turns * 2*np.pi + seed
    rad = r * (0.55 + 0.45*np.sin(t*3 + seed))
    x = np.cos(ang) * rad
    y = t * 14 - 3
    z = np.sin(ang) * rad * 0.65
    m = np.array([m_func(ti) for ti in t])
    return x, y, z, m, t

helices = [
    ('中国', gen_helix(7, 5, m_china, 0)),
    ('西方', gen_helix(6, 4.2, m_west, 2.3)),
    ('全球南方', gen_helix(6, 5.8, m_south, 4.5)),
    ('可能性', gen_helix(5, 3.2, m_possible, 1.2)),
]

fig = plt.figure(figsize=(12, 14), facecolor='#faf6ee')
ax = fig.add_subplot(111, projection='3d', facecolor='#faf6ee')

for name, (x, y, z, m, t) in helices:
    for i in range(len(t)-1):
        lw = max(1.5, 6.5 * (0.4 + t[i]*0.8))
        c = m_color((m[i]+m[i+1])/2)
        ax.plot(x[i:i+2], z[i:i+2], y[i:i+2], color=c, linewidth=lw, alpha=0.9, solid_capstyle='round')
    for i in range(len(t)-1):
        if m[i] > 0.3:
            lw = max(1.5, 6.5 * (0.4 + t[i]*0.8)) * 2.5
            c = m_color((m[i]+m[i+1])/2)
            ax.plot(x[i:i+2], z[i:i+2], y[i:i+2], color=c, linewidth=lw, alpha=0.07, solid_capstyle='round')

cn = helices[0][1]
high_idx = np.where(cn[3] > 0.5)[0]
for hi, (name, h) in enumerate(helices[1:]):
    low_idx = np.where(h[3] < -0.2)[0]
    if len(high_idx) > 0 and len(low_idx) > 0:
        ai = high_idx[len(high_idx)//2 + hi*8]
        bi = low_idx[len(low_idx)//3]
        a = np.array([cn[0][ai], cn[2][ai], cn[1][ai]])
        b = np.array([h[0][bi], h[2][bi], h[1][bi]])
        mid = (a + b) / 2 + np.array([3, 0, 4])
        ts = np.linspace(0, 1, 50)
        curve = np.array([(1-ti)**2*a + 2*(1-ti)*ti*mid + ti**2*b for ti in ts])
        for j in range(0, len(ts)-1, 2):
            ax.plot(curve[j:j+2,0], curve[j:j+2,1], curve[j:j+2,2],
                   color=C_GOLD, linewidth=2, alpha=0.55, dashes=[4,3])

rng = np.random.RandomState(42)
for name, (x, y, z, m, t) in helices:
    idx = np.where(m > 0.45)[0]
    if len(idx) > 0:
        sel = idx[rng.choice(len(idx), min(40, len(idx)), replace=False)]
        ax.scatter(x[sel], z[sel], y[sel],
                  c=[m_color(m[i]) for i in sel], s=30, alpha=0.7, depthshade=False)

ax.plot([0,0], [0,0], [-3, 12], color=(0.63,0.55,0.39,0.25), linewidth=1.2, linestyle='--')

ax.text(0, 0, 12.8, '践演 ↑ 时间', fontsize=13, color='#5a4a3a', ha='center', fontproperties=FP_B)
ax.text(5.5, 0, 6.5, '人民在主位', fontsize=10, color='#c43a1e', ha='center', alpha=0.85, fontproperties=FP)
ax.text(-2, 2, 8, '火种迁移', fontsize=9, color='#9a7a2a', ha='center', alpha=0.8, fontproperties=FP)

ax.view_init(elev=12, azim=-55)
ax.set_xlim(-8, 8); ax.set_ylim(-5.5, 5.5); ax.set_zlim(-3.5, 13)
ax.axis('off')

fig.suptitle('践演 — 迁演 的磁极螺旋', fontsize=20, fontweight='bold', color='#3a2e1e', y=0.96, fontproperties=FP_B)
fig.text(0.5, 0.93, '历史是力的生命化在时空中的展开：多条脉络在空间中分叉交织（迁演），在时间中沉积消息（践演），磁极可翻转',
         fontsize=10, color='#7a6e5a', ha='center', fontproperties=FP)

legend_elements = [
    Line2D([0],[0], color=C_WARM, linewidth=5, label='磁极朝上 · 阳息阴消 · M值升 · 人民在主位'),
    Line2D([0],[0], color=C_COLD, linewidth=5, label='磁极朝下 · 阴息阳消 · M值降 · 活劳动被支配'),
    Line2D([0],[0], color=C_GOLD, linewidth=2, linestyle='--', label='金线 = 火种迁移 · 历史资源在另一处重新激活'),
]
leg = ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.08),
         fontsize=10, frameon=True, facecolor='#fffdf7', edgecolor='#d4c8a8',
         title='螺旋线 = 践演（时间流淌） · 分叉交织 = 迁演（空间展开）', title_fontsize=9,
         prop=FP)
leg.get_title().set_fontproperties(FP)

plt.tight_layout()
out = '/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun/docs/visualizations/践演迁演磁极螺旋.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor='#faf6ee')
print("Saved:", out)
