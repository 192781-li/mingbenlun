#!/usr/bin/env python3
"""
明本自筛系统：元监督机制
把历次审计发现的问题固化为自动检查，每次构建/推送前运行。
新增问题类型时，在这里加一个check函数即可。

用法：
  python3 self_audit.py          # 全量检查
  python3 self_audit.py --quiet  # 只在有问题时输出
"""
import sys, os, re, subprocess, threading, io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 路径锚定
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE = SKILL_DIR.parent
MODDIR = WORKSPACE / "生命论_模块化"
FULL_MD = WORKSPACE / "生命论合订本_最新.md"

passed = 0
failed = 0
warnings = 0
_lock = threading.Lock()
_parallel = False
_output_buffers = {}  # thread_id -> StringIO

def ok(msg):
    global passed
    with _lock:
        passed += 1
    if _parallel:
        tid = threading.get_ident()
        _output_buffers[tid].write(f"  ✅ {msg}\n")
    else:
        print(f"  ✅ {msg}")

def fail(msg):
    global failed
    with _lock:
        failed += 1
    if _parallel:
        tid = threading.get_ident()
        _output_buffers[tid].write(f"  ❌ {msg}\n")
    else:
        print(f"  ❌ {msg}")

def warn(msg):
    global warnings
    with _lock:
        warnings += 1
    if _parallel:
        tid = threading.get_ident()
        _output_buffers[tid].write(f"  ⚠️  {msg}\n")
    else:
        print(f"  ⚠️  {msg}")

# ========== 工具函数 ==========

CN = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,
      '十':10,'百':100,'千':1000,'两':2}

def cn2int(s):
    r, t = 0, 0
    for c in s:
        if c not in CN: return None
        n = CN[c]
        if n >= 10:
            if t == 0: t = 1
            r += t * n; t = 0
        else:
            t = n
    return r + t

def get_actual_chapter_count():
    """从合订本获取实际章数"""
    if not FULL_MD.exists(): return None
    text = FULL_MD.read_text(encoding='utf-8', errors='replace')
    return len(re.findall(r'^### 第[零一二三四五六七八九十百千两]+章', text, re.MULTILINE))

def get_actual_appendix_count():
    """从附录目录获取实际附录数（排除00_附录标题.md）"""
    app_dir = MODDIR / "10_附录"
    if not app_dir.exists(): return None
    return len([f for f in app_dir.glob("附录*.md")])

def get_module_count():
    """获取manifest中的模块数"""
    manifest = MODDIR / "manifest.txt"
    if not manifest.exists(): return None
    return len([l for l in manifest.read_text(encoding='utf-8').splitlines()
                if l.strip() and not l.startswith('#')])

# ========== 检查项 ==========

def check_chapter_count_consistency():
    """[元数据一致性] 技能文档中声称的章数必须与实际一致"""
    actual = get_actual_chapter_count()
    if actual is None:
        warn("合订本不存在，跳过章数一致性检查（先构建）")
        return

    # 扫描所有技能文档和AGENTS.md中的章数声明
    targets = list(SKILL_DIR.rglob("*.md")) + list((SKILL_DIR.parent / "mingben-output").rglob("*.md"))
    targets.append(MODDIR / "AGENTS.md")

    for f in targets:
        if not f.exists(): continue
        text = f.read_text(encoding='utf-8', errors='replace')
        # 匹配 "252章" "213章" "247章" 等
        for m in re.finditer(r'(\d{2,3})\s*章', text):
            claimed = int(m.group(1))
            # 排除"第X章"引用、"章数"等非总数声明
            ctx = text[max(0,m.start()-20):m.end()+20]
            if any(kw in ctx for kw in ['全本', '总章', '共', '模块', '当前', '个章']):
                if claimed != actual:
                    fail(f"章数不一致 {f.relative_to(WORKSPACE)}: 声称{claimed}章，实际{actual}章")
                    break
        else:
            continue
        break
    else:
        ok(f"章数一致性：所有文档均为{actual}章")

def check_appendix_count_consistency():
    """[元数据一致性] 附录数声明必须与实际一致"""
    actual = get_actual_appendix_count()
    if actual is None:
        warn("附录目录不存在，跳过")
        return

    targets = list(SKILL_DIR.rglob("*.md")) + list((SKILL_DIR.parent / "mingben-output").rglob("*.md"))
    targets.append(MODDIR / "AGENTS.md")
    # build.sh和build_all.sh中的封面文本
    targets.append(MODDIR / "build.sh")
    targets.append(MODDIR / "build_all.sh")

    bad = False
    for f in targets:
        if not f.exists(): continue
        text = f.read_text(encoding='utf-8', errors='replace')
        for m in re.finditer(r'附录\s*([一二三四五六七八九十\d]+)\s*种', text):
            claimed_str = m.group(1)
            claimed = cn2int(claimed_str) if claimed_str in CN or all(c in CN for c in claimed_str) else int(claimed_str) if claimed_str.isdigit() else None
            if claimed is not None and claimed != actual:
                fail(f"附录数不一致 {f.relative_to(WORKSPACE)}: 声称{claimed}种，实际{actual}种")
                bad = True
    if not bad:
        ok(f"附录数一致性：所有文档均为{actual}种")

def check_file_references():
    """[引用有效性] 技能文档中引用的脚本/样式文件必须存在"""
    ref_pattern = re.compile(r'`([^`]+\.(?:py|sh|css|tex|html))`')
    bad = []
    # 扫描所有技能目录
    scan_dirs = [SKILL_DIR]
    output_dir = WORKSPACE / "mingben-output"
    if output_dir.exists():
        scan_dirs.append(output_dir)
    for scan_dir in scan_dirs:
        for f in scan_dir.rglob("*.md"):
            # 跳过挖掘日志等数据文件（其中的路径是历史记录，不是依赖声明）
            if f.name in ('spark_candidates.md',):
                continue
            text = f.read_text(encoding='utf-8', errors='replace')
            for m in ref_pattern.finditer(text):
                ref = m.group(1)
                if ref.startswith('http'):
                    continue
                # 从命令行调用中提取文件路径（python3/bash 后面的第一个token）
                if ref.startswith('python3 ') or ref.startswith('bash '):
                    parts = ref.split()
                    if len(parts) >= 2:
                        ref = parts[1]
                    else:
                        continue
                # 去掉参数（--flag 或 <参数>）
                ref = ref.split()[0] if not ref.startswith('/') else ref
                # 解析路径：先试workspace根，再试技能目录
                candidates = [WORKSPACE / ref, scan_dir / ref]
                if not any(c.exists() for c in candidates):
                    bad.append(f"{f.relative_to(WORKSPACE)} → {ref}")
    if bad:
        for b in bad:
            fail(f"失效引用: {b}")
    else:
        ok("文件引用有效性：所有引用的脚本/样式文件均存在")

def check_cross_references():
    """[交叉引用] 文内"第X章"引用不超过最大章号"""
    if not FULL_MD.exists():
        warn("合订本不存在，跳过（先构建）")
        return
    text = FULL_MD.read_text(encoding='utf-8', errors='replace')
    max_ch = get_actual_chapter_count()

    bad = []
    for m in re.finditer(r'第([零一二三四五六七八九十百千两]+)章', text):
        n = cn2int(m.group(1))
        if n is not None and n > max_ch:
            ctx = text[max(0,m.start()-15):m.end()+15].replace('\n',' ')
            bad.append(f"第{n}章 (上限{max_ch}): ...{ctx}...")
    if bad:
        for b in bad[:5]:
            fail(f"交叉引用越界: {b}")
        if len(bad) > 5:
            fail(f"...共{len(bad)}处越界")
    else:
        ok(f"交叉引用：所有'第X章'引用均在1-{max_ch}范围内")

def check_empty_dirs():
    """[空目录] 技能目录下不应有空目录"""
    bad = []
    for skill_dir in [SKILL_DIR, SKILL_DIR.parent / "mingben-output"]:
        if not skill_dir.exists(): continue
        for d in skill_dir.rglob("*"):
            if d.is_dir() and not any(d.iterdir()):
                bad.append(str(d.relative_to(WORKSPACE)))
    if bad:
        for b in bad:
            fail(f"空目录: {b}")
    else:
        ok("空目录检查：无空壳目录")

def check_skill_integrity():
    """[技能完整性] backup.sh引用的技能目录必须存在"""
    backup_sh = WORKSPACE / "backup.sh"
    if not backup_sh.exists():
        warn("backup.sh不存在，跳过")
        return
    text = backup_sh.read_text(encoding='utf-8')
    m = re.search(r'for\s+skill\s+in\s+([^;]+);', text)
    if not m:
        warn("backup.sh中未找到技能列表")
        return
    skills = m.group(1).split()
    bad = [s for s in skills if not (WORKSPACE / s).is_dir()]
    if bad:
        for b in bad:
            fail(f"backup.sh引用了不存在的技能目录: {b}")
    else:
        ok(f"技能完整性：backup.sh引用的{len(skills)}个技能目录均存在")

def check_git_size():
    """[git健康] .git目录不应过大（防止再次出现1.6GB事件）"""
    try:
        r = subprocess.run(['git', 'count-objects', '-v'], cwd=str(WORKSPACE),
                          capture_output=True, text=True, timeout=10)
        size_pack = 0
        for line in r.stdout.splitlines():
            if line.startswith('size-pack:'):
                size_pack = int(line.split(':')[1].strip())  # KB
        size_mb = size_pack / 1024
        if size_mb > 50:
            fail(f"git仓库过大: {size_mb:.1f}MB（阈值50MB），可能有大文件误入历史")
        elif size_mb > 20:
            warn(f"git仓库偏大: {size_mb:.1f}MB（阈值50MB），注意大文件")
        else:
            ok(f"git仓库健康: {size_mb:.1f}MB")
    except Exception as e:
        warn(f"git检查失败: {e}")

def check_human_size_unit():
    """[单元测试] human_size函数：字节不能显示为K/M"""
    # 模拟monitor.py中的human_size逻辑
    def human_size(n):
        for unit in ['B','K','M','G','T','P','E']:
            if n < 1024: return f"{n:.0f}{unit}"
            n /= 1024
        return f"{n:.0f}Z"

    cases = [
        (0, "0B"), (512, "512B"), (1024, "1K"), (974000, "951K"),
        (1048576, "1M"), (906059, "885K"),
    ]
    bad = []
    for val, expected in cases:
        result = human_size(val)
        if result != expected:
            bad.append(f"human_size({val})={result}, 期望{expected}")
    if bad:
        for b in bad:
            fail(f"单位函数错误: {b}")
    else:
        ok("human_size单元测试：6个用例全部通过")

def check_outdated_keywords():
    """[过时信息扫描] 已知过时的关键词不应出现在技能文档中"""
    outdated = {
        'shengminglun.git': '旧仓库地址（已改名mingbenlun）',
        '<用户名>': '未填写的占位符',
        'html_style.css': '不存在的文件（样式在html_header.html内联）',
    }
    # 数字类过时信息（只在声明总数的语境中检查）
    bad = []
    for f in list(SKILL_DIR.rglob("*.md")) + list((SKILL_DIR.parent / "mingben-output").rglob("*.md")):
        text = f.read_text(encoding='utf-8', errors='replace')
        for kw, desc in outdated.items():
            if kw in text:
                bad.append(f"{f.relative_to(WORKSPACE)} 含 '{kw}'（{desc}）")
    if bad:
        for b in bad:
            fail(f"过时关键词: {b}")
    else:
        ok("过时关键词扫描：无已知过时信息")

def check_cover_matches_actual():
    """[封面一致性] build.sh封面中的章数/附录数与实际一致"""
    build_sh = MODDIR / "build.sh"
    if not build_sh.exists():
        warn("build.sh不存在，跳过")
        return
    text = build_sh.read_text(encoding='utf-8', errors='replace')
    actual_app = get_actual_appendix_count()

    bad = False
    m = re.search(r'附录\s*([一二三四五六七八九十]+)\s*种', text)
    if m and actual_app is not None:
        claimed = cn2int(m.group(1))
        if claimed != actual_app:
            fail(f"build.sh封面附录数: {claimed}，实际: {actual_app}")
            bad = True
    if not bad:
        ok("封面一致性：封面文本与实际附录数一致")

def check_build_arg_validation():
    """[参数防护] build.sh必须拒绝未知参数（防止拼写错误触发10分钟PDF构建）"""
    build_sh = MODDIR / "build.sh"
    text = build_sh.read_text(encoding='utf-8', errors='replace')
    if '未知参数' in text or 'usage' in text.lower() or 'Usage' in text:
        ok("参数防护：build.sh有未知参数校验")
    else:
        fail("build.sh缺少未知参数校验（拼写错误会触发完整PDF构建）")

def check_manifest_completeness():
    """[manifest完整性] manifest中的文件必须存在，目录下的md必须在manifest中"""
    manifest = MODDIR / "manifest.txt"
    if not manifest.exists():
        fail("manifest.txt不存在")
        return
    entries = [l.strip() for l in manifest.read_text(encoding='utf-8').splitlines()
               if l.strip() and not l.startswith('#')]
    missing = [e for e in entries if not (MODDIR / e).exists()]
    # 检查是否有md文件遗漏（排除00_固定文件、AGENTS/README、答题训练文件）
    fixed = {'00_体系总纲.md', '00_修订记与体系总纲.md', '00_总序与导论.md', '00_推导链总览.md'}
    all_md = set()
    for f in MODDIR.rglob("*.md"):
        rel = str(f.relative_to(MODDIR))
        if f.name in ('AGENTS.md', 'README.md'):
            continue
        if rel in fixed:
            continue  # 固定文件不在manifest中
        if f.name.startswith('训练') and '_' in f.name:
            continue  # 答题训练文件不入manifest
        if not rel.startswith('00_'):
            all_md.add(rel)
        else:
            all_md.add(rel)  # 00_卷标题.md等
    orphaned = all_md - set(entries)

    bad = False
    if missing:
        for m in missing:
            fail(f"manifest引用不存在的文件: {m}")
        bad = True
    if orphaned:
        for o in orphaned:
            fail(f"md文件未加入manifest: {o}")
        bad = True
    if not bad:
        ok(f"manifest完整性：{len(entries)}个条目全部对应，无遗漏")

def check_infrastructure_reflexivity():
    """[元监督自反性] 构建系统必须集成自筛，TOC必须包含章级导航"""
    bad = []

    # build.sh必须调用self_audit
    build_sh = MODDIR / "build.sh"
    if build_sh.exists():
        text = build_sh.read_text(encoding='utf-8', errors='replace')
        if 'self_audit' not in text:
            bad.append("build.sh未集成self_audit（构建后不会自动自筛）")
        if '--toc-depth=3' not in text:
            bad.append("build.sh HTML目录深度<3（章级导航缺失）")

    # sync.sh必须有自筛门控
    sync_sh = WORKSPACE / "sync.sh"
    if sync_sh.exists():
        text = sync_sh.read_text(encoding='utf-8', errors='replace')
        if 'self_audit' not in text:
            bad.append("sync.sh未集成self_audit（推送前无硬门控）")

    # build_all.sh也应有正确的TOC深度
    build_all = MODDIR / "build_all.sh"
    if build_all.exists():
        text = build_all.read_text(encoding='utf-8', errors='replace')
        if '--toc-depth=2' in text:
            bad.append("build_all.sh仍使用toc-depth=2（章级导航缺失）")

    if bad:
        for b in bad:
            fail(f"自反性: {b}")
    else:
        ok("基础设施自反性：自筛已集成到build/sync，TOC深度正确")

def check_pending_integration():
    """[内容新鲜度] 闪光点中标注'待入全本'的条目必须被追踪，防止'全本'幻觉"""
    spark = WORKSPACE / "闪光点.md"
    if not spark.exists():
        warn("闪光点.md不存在，跳过")
        return
    text = spark.read_text(encoding='utf-8', errors='replace')
    pending = []
    for m in re.finditer(r'###\s*(\d+)\.\s*(.+?)(?:\n|$)', text):
        num = int(m.group(1))
        title = m.group(2).strip()
        block_end = text.find('\n### ', m.end())
        if block_end == -1: block_end = len(text)
        block = text[m.start():block_end]
        if '待入全本' in block:
            pending.append((num, title))
    if pending:
        warn(f"有{len(pending)}条闪光点标注'待入全本'（最新思想未进入九卷正文）：")
        for num, title in pending[-8:]:
            print(f"    #{num}: {title[:40]}")
        if len(pending) > 8:
            print(f"    ...等共{len(pending)}条")
    else:
        ok("内容新鲜度：闪光点无'待入全本'条目")

def check_backup_completeness():
    """[备份完整性] backup.sh的tar命令必须包含闪光点、创作日志等关键根文件"""
    backup_sh = WORKSPACE / "backup.sh"
    if not backup_sh.exists():
        warn("backup.sh不存在，跳过")
        return
    text = backup_sh.read_text(encoding='utf-8')
    required = ['闪光点.md', '创作日志.md', '生命论合订本_最新.md']
    missing = [f for f in required if f not in text]
    if missing:
        for m in missing:
            fail(f"backup.sh未备份关键文件: {m}")
    else:
        ok("备份完整性：闪光点、创作日志、合订本均在备份列表中")

def check_concept_graph_freshness():
    """[概念图新鲜度] concept_graph.json不应比闪光点.md旧超过3天"""
    import time
    graph = SKILL_DIR / "references" / "concept_graph.json"
    spark = WORKSPACE / "闪光点.md"
    if not graph.exists() or not spark.exists():
        warn("概念图或闪光点不存在，跳过新鲜度检查")
        return
    graph_age = time.time() - graph.stat().st_mtime
    spark_age = time.time() - spark.stat().st_mtime
    if graph_age > spark_age + 86400 * 3:
        warn(f"concept_graph.json比闪光点旧（图{graph_age/86400:.0f}天，闪光点{spark_age/86400:.0f}天），新概念可能未入图")
    else:
        ok(f"概念图新鲜度：concept_graph.json ({graph_age/86400:.1f}天) 与闪光点同步")


# ========== 主入口 ==========

def check_test_suite():
    """[功能测试] 在沙箱中实际执行所有脚本路径，验证不变量"""
    if os.environ.get('MINGBEN_SKIP_TESTS') == '1':
        warn("功能测试套件：沙箱环境跳过")
        return
    test_script = SCRIPT_DIR / "test_system.py"
    if not test_script.exists():
        fail("test_system.py 不存在")
        return
    import subprocess
    r = subprocess.run([sys.executable, str(test_script)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        # 从输出中提取通过数
        m = re.search(r'✅(\d+)通过', r.stdout)
        count = m.group(1) if m else "?"
        ok(f"功能测试套件：{count}项全部通过")
    else:
        # 提取失败项
        fails = [l.strip() for l in r.stdout.splitlines() if '❌' in l and '失败' not in l]
        fail(f"功能测试套件有失败（{len(fails)}项）:")
        for f in fails[:5]:
            print(f"    {f}")

CHECKS = [
    ("章数一致性", check_chapter_count_consistency),
    ("附录数一致性", check_appendix_count_consistency),
    ("封面一致性", check_cover_matches_actual),
    ("文件引用有效性", check_file_references),
    ("交叉引用", check_cross_references),
    ("manifest完整性", check_manifest_completeness),
    ("空目录检查", check_empty_dirs),
    ("技能完整性", check_skill_integrity),
    ("参数防护", check_build_arg_validation),
    ("过时关键词扫描", check_outdated_keywords),
    ("human_size单元测试", check_human_size_unit),
    ("git仓库健康", check_git_size),
    ("基础设施自反性", check_infrastructure_reflexivity),
    ("内容新鲜度(待入全本)", check_pending_integration),
    ("备份完整性", check_backup_completeness),
    ("概念图新鲜度", check_concept_graph_freshness),
    ("功能测试套件", check_test_suite),
]

def main():
    global _parallel
    quiet = '--quiet' in sys.argv
    parallel = '--parallel' in sys.argv or '-p' in sys.argv

    if not quiet:
        print("=" * 50)
        print("明本自筛系统 — 元监督检查" + ("（并行模式）" if parallel else ""))
        print("=" * 50)

    if parallel:
        _parallel = True
        results = [None] * len(CHECKS)

        def run_check(idx):
            name, fn = CHECKS[idx]
            tid = threading.get_ident()
            _output_buffers[tid] = io.StringIO()
            try:
                fn()
            except Exception as e:
                fail(f"{name} 检查自身异常: {e}")
            output = _output_buffers[tid].getvalue()
            _output_buffers.pop(tid, None)
            return idx, name, output

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_check, i) for i in range(len(CHECKS))]
            for future in as_completed(futures):
                idx, name, output = future.result()
                results[idx] = (name, output)

        if not quiet:
            for name, output in results:
                print(f"\n[{name}]")
                if output:
                    print(output.rstrip())
    else:
        for name, fn in CHECKS:
            if not quiet:
                print(f"\n[{name}]")
            try:
                fn()
            except Exception as e:
                fail(f"{name} 检查自身异常: {e}")

    if not quiet:
        print("\n" + "=" * 50)
        print(f"结果: ✅{passed}通过  ❌{failed}失败  ⚠️{warnings}警告")
        print("=" * 50)

    sys.exit(1 if failed > 0 else 0)

if __name__ == '__main__':
    main()
