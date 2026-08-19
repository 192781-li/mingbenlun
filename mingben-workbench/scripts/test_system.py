#!/usr/bin/env python3
"""
明本系统测试套件：在临时沙箱中实际执行所有脚本路径，验证不变量。
不是读代码猜问题，是真跑。

用法：python3 test_system.py
"""
import sys, os, re, shutil, tempfile, subprocess
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent
MODDIR = WORKSPACE / "生命论_模块化"
SCRIPTS = WORKSPACE / "mingben-workbench" / "scripts"

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  ✅ {msg}")

def fail(msg):
    global failed
    failed += 1
    print(f"  ❌ {msg}")

def section(name):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")

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

def int2cn(n):
    digits = '零一二三四五六七八九'
    if n < 10: return digits[n]
    if n == 10: return '十'
    if n < 20: return '十' + (digits[n%10] if n%10 else '')
    if n < 100:
        return digits[n//10] + '十' + (digits[n%10] if n%10 else '')
    if n < 1000:
        r = digits[n//100] + '百'; rest = n % 100
        if rest == 0: return r
        if rest < 10: return r + '零' + digits[rest]
        if rest < 20: return r + '一' + int2cn(rest)
        return r + int2cn(rest)
    return str(n)

def parse_chapters(text):
    """返回 {编号: 标题}"""
    chs = {}
    for m in re.finditer(r'^### 第([零一二三四五六七八九十百千两]+)章\s+(.+)$', text, re.MULTILINE):
        n = cn2int(m.group(1))
        chs[n] = m.group(2).strip()
    return chs

def verify_continuous(chs, label=""):
    """验证章节编号1..N连续无重复"""
    nums = sorted(chs.keys())
    if not nums:
        fail(f"{label}: 没有章节")
        return False
    if nums[0] != 1:
        fail(f"{label}: 第一章编号是{nums[0]}不是1")
        return False
    expected = list(range(1, len(nums)+1))
    if nums != expected:
        gaps = [i for i in range(len(nums)) if nums[i] != i+1]
        fail(f"{label}: 编号不连续，前几个问题位置: {[(nums[i], i+1) for i in gaps[:3]]}")
        return False
    return True

def verify_cross_refs(text, max_ch, label=""):
    """验证所有交叉引用指向存在的章节"""
    bad = []
    for m in re.finditer(r'第([零一二三四五六七八九十百千两]+)章', text):
        n = cn2int(m.group(1))
        if n is not None and n > max_ch:
            bad.append(n)
    if bad:
        fail(f"{label}: {len(bad)}个交叉引用越界（最大{max_ch}章）: {bad[:3]}")
        return False
    return True

# ========== 测试1: cn2int/int2cn 往返 ==========

def test_number_conversion():
    section("测试1: 中文数字转换往返")
    all_ok = True
    for n in range(1, 300):
        cn = int2cn(n)
        back = cn2int(cn)
        if back != n:
            fail(f"数字转换往返失败: {n} → '{cn}' → {back}")
            all_ok = False
            break
    if all_ok:
        ok(f"1-299中文数字往返全部正确")

    # 边界值
    for n in [1, 9, 10, 11, 19, 20, 99, 100, 101, 110, 111, 199, 200, 201, 252, 999]:
        cn = int2cn(n)
        back = cn2int(cn)
        if back != n:
            fail(f"边界值失败: {n} → '{cn}' → {back}")
            all_ok = False
    if all_ok:
        ok("边界值全部正确")

# ========== 测试2: auto_merge.py 完整功能测试 ==========

def test_auto_merge():
    section("测试2: auto_merge.py 沙箱测试")

    # 创建临时模块化目录
    tmpdir = tempfile.mkdtemp(prefix="mingben_test_")
    moddir = Path(tmpdir) / "生命论_模块化"
    moddir.mkdir()

    try:
        # 创建3个卷，每个卷2篇，每篇2章 = 12章
        manifest_lines = []
        for juan in range(1, 4):
            juan_dir = moddir / f"{juan:02d}_卷{juan}"
            juan_dir.mkdir()
            for pian in range(1, 3):
                pian_num = int2cn(pian)
                fname = f"篇{pian_num}_测试篇{juan}-{pian}.md"
                content = f"## 第{pian_num}篇 测试篇{juan}-{pian}\n\n"
                ch_in_pian = 2
                for c in range(ch_in_pian):
                    ch_num = (juan-1)*4 + (pian-1)*2 + c + 1
                    ch_cn = int2cn(ch_num)
                    content += f"### 第{ch_cn}章 标题{ch_num}\n\n这是第{ch_cn}章的内容。参见下一章。\n\n"
                (juan_dir / fname).write_text(content, encoding='utf-8')
                manifest_lines.append(f"{juan:02d}_卷{juan}/{fname}")

        # 固定文件
        (moddir / "00_总序与导论.md").write_text("# 总序\n\n### 序章 开始\n\n开始内容。\n", encoding='utf-8')
        (moddir / "manifest.txt").write_text('\n'.join(manifest_lines) + '\n', encoding='utf-8')

        # 复制auto_merge.py到临时位置并修改BASE路径
        merge_script = moddir / "auto_merge.py"
        orig_script = (MODDIR / "auto_merge.py").read_text(encoding='utf-8')
        merge_script.write_text(orig_script, encoding='utf-8')

        def run_merge(args, input_text=None):
            r = subprocess.run(
                [sys.executable, str(merge_script)] + args,
                capture_output=True, text=True, cwd=str(tmpdir),
                input=input_text, timeout=30
            )
            return r

        def build_full():
            """合并所有模块"""
            parts = [(moddir / "00_总序与导论.md").read_text(encoding='utf-8')]
            for line in manifest_lines:
                parts.append((moddir / line).read_text(encoding='utf-8'))
            return '\n\n'.join(parts)

        # --- 2a. 验证初始状态 ---
        text = build_full()
        chs = parse_chapters(text)
        if verify_continuous(chs, "初始状态"):
            ok(f"初始12章编号连续")
        if verify_cross_refs(text, 12, "初始状态"):
            ok("初始交叉引用有效")

        # --- 2b. 在中间插入新章节（第3章位置）---
        insert_file = Path(tmpdir) / "新章节.md"
        insert_file.write_text("### 第三章 新插入的章\n\n这是新插入的第三章内容。\n\n", encoding='utf-8')
        r = run_merge([str(insert_file), "--no-build"])
        if r.returncode != 0:
            fail(f"插入章节失败: {r.stderr[-200:]}")
        else:
            # 重新读取manifest（可能被auto_merge修改）
            manifest_lines = [l.strip() for l in (moddir / "manifest.txt").read_text(encoding='utf-8').splitlines() if l.strip()]
            text = build_full()
            chs = parse_chapters(text)
            if verify_continuous(chs, "插入后"):
                ok("插入后13章编号连续")
            if 3 in chs and chs[3] == "新插入的章":
                ok("新章节正确编号为第三章")
            else:
                fail(f"新章节位置错误: 第3章标题='{chs.get(3, '不存在')}'")
            # 验证旧章节标题保留
            expected_titles = {1:"标题1", 2:"标题2", 4:"标题3", 5:"标题4", 6:"标题5",
                             7:"标题6", 8:"标题7", 9:"标题8", 10:"标题9", 11:"标题10",
                             12:"标题11", 13:"标题12"}
            title_ok = True
            for n, t in expected_titles.items():
                if chs.get(n) != t:
                    fail(f"标题错位: 第{n}章应为'{t}'，实际'{chs.get(n, '?')}'")
                    title_ok = False
            if title_ok:
                ok("所有旧章节标题正确顺延")
            if verify_cross_refs(text, 13, "插入后"):
                ok("插入后交叉引用有效")

        # --- 2c. 替换已有章节 ---
        replace_file = Path(tmpdir) / "替换章节.md"
        replace_file.write_text("### 第一章 替换后的标题\n\n这是替换后的内容。\n\n", encoding='utf-8')
        r = run_merge([str(replace_file), "--no-build"])
        if r.returncode != 0:
            fail(f"替换章节失败: {r.stderr[-200:]}")
        else:
            manifest_lines = [l.strip() for l in (moddir / "manifest.txt").read_text(encoding='utf-8').splitlines() if l.strip()]
            text = build_full()
            chs = parse_chapters(text)
            if verify_continuous(chs, "替换后"):
                ok("替换后章节编号仍连续")
            if chs.get(1) == "替换后的标题":
                ok("章节替换成功")
            else:
                fail(f"替换失败: 第1章标题='{chs.get(1, '?')}'")

        # --- 2d. 在末尾追加章节 ---
        append_file = Path(tmpdir) / "追加章节.md"
        append_file.write_text("### 第十四章 追加的章\n\n这是追加的最后一章。\n\n", encoding='utf-8')
        r = run_merge([str(append_file), "--no-build"])
        if r.returncode != 0:
            fail(f"追加章节失败: {r.stderr[-200:]}")
        else:
            manifest_lines = [l.strip() for l in (moddir / "manifest.txt").read_text(encoding='utf-8').splitlines() if l.strip()]
            text = build_full()
            chs = parse_chapters(text)
            if verify_continuous(chs, "追加后"):
                ok(f"追加后{len(chs)}章编号连续")
            if chs.get(len(chs)) == "追加的章":
                ok("末尾追加成功")

        # --- 2e. --validate ---
        r = run_merge(["--validate"])
        if r.returncode == 0 and "连续" in r.stdout:
            ok("--validate 通过")
        else:
            fail(f"--validate 失败: {r.stdout} {r.stderr}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ========== 测试2b: 跨模块引用与边界 ==========

def test_auto_merge_cross_module_refs():
    """跨模块引用更新 + 同模块多章顺延 + 插入第1章边界"""
    section("测试2b: auto_merge 跨模块引用与边界条件")

    tmpdir = tempfile.mkdtemp(prefix="mingben_xref_")
    moddir = Path(tmpdir) / "生命论_模块化"
    moddir.mkdir()

    try:
        (moddir / "00_总序与导论.md").write_text("", encoding='utf-8')
        (moddir / "manifest.txt").write_text("01/f1.md\n02/f2.md\n03/f3.md\n", encoding='utf-8')
        (moddir / "01").mkdir()
        (moddir / "02").mkdir()
        (moddir / "03").mkdir()
        (moddir / "01/f1.md").write_text(
            "### 第一章 标题1\n\n内容，参见第五章。\n\n### 第二章 标题2\n\n内容2\n", encoding='utf-8')
        (moddir / "02/f2.md").write_text(
            "### 第三章 标题3\n\n内容3\n\n### 第四章 标题4\n\n内容4\n", encoding='utf-8')
        (moddir / "03/f3.md").write_text(
            "### 第五章 标题5\n\n内容5\n\n### 第六章 标题6\n\n内容6\n", encoding='utf-8')

        merge_script = moddir / "auto_merge.py"
        merge_script.write_text((MODDIR / "auto_merge.py").read_text(encoding='utf-8'), encoding='utf-8')

        def run_merge(args):
            return subprocess.run([sys.executable, str(merge_script)] + args,
                capture_output=True, text=True, cwd=str(tmpdir), timeout=30)

        def build_full():
            parts = [(moddir / "00_总序与导论.md").read_text(encoding='utf-8')]
            for line in (moddir / "manifest.txt").read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line:
                    parts.append((moddir / line).read_text(encoding='utf-8'))
            return '\n\n'.join(parts)

        # 在第3章位置插入新章
        ins = Path(tmpdir) / "ins.md"
        ins.write_text("### 第三章 新章X\n\n新内容\n", encoding='utf-8')
        r = run_merge([str(ins), "--no-build"])
        if r.returncode != 0:
            fail(f"插入失败: {r.stderr[-300:]}")
        else:
            text = build_full()
            chs = parse_chapters(text)
            if verify_continuous(chs, "跨模块插入后"):
                ok("跨模块插入后7章连续")
            if "参见第六章" in text and "参见第五章" not in text:
                ok("跨模块引用正确更新（第五章→第六章）")
            else:
                fail(f"跨模块引用未更新: 五={'参见第五章' in text} 六={'参见第六章' in text}")
            if chs.get(3) == "新章X" and chs.get(6) == "标题5" and chs.get(7) == "标题6":
                ok("所有标题位置正确")
            else:
                fail(f"标题错位: {dict(sorted(chs.items()))}")

        # 在第1章位置插入（边界条件）
        ins2 = Path(tmpdir) / "ins2.md"
        ins2.write_text("### 第一章 最前章\n\n最前内容\n", encoding='utf-8')
        r = run_merge([str(ins2), "--no-build"])
        if r.returncode != 0:
            fail(f"第1章插入失败: {r.stderr[-300:]}")
        else:
            text = build_full()
            chs = parse_chapters(text)
            if verify_continuous(chs, "第1章插入后"):
                ok("第1章位置插入后8章连续")
            if chs.get(1) == "最前章" and chs.get(2) == "标题1":
                ok("第1章边界插入正确")
            else:
                fail(f"第1章插入标题错位: {dict(sorted(chs.items()))}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ========== 测试3: self_audit.py 抓bug能力 ==========

def test_self_audit_detection():
    section("测试3: self_audit.py 抓bug能力")

    # 在临时副本中注入各种问题，验证自筛能抓到
    tmpdir = tempfile.mkdtemp(prefix="mingben_audit_")
    try:
        # 复制技能脚本
        scripts_dst = Path(tmpdir) / "scripts"
        shutil.copytree(SCRIPTS, scripts_dst)

        # 创建最小化的workspace结构
        moddir = Path(tmpdir) / "生命论_模块化"
        moddir.mkdir()
        (moddir / "manifest.txt").write_text("", encoding='utf-8')
        (moddir / "00_总序与导论.md").write_text("", encoding='utf-8')
        # 复制真实build.sh（包含参数校验、自筛集成、TOC深度3）
        shutil.copy2(MODDIR / "build.sh", moddir / "build.sh")
        shutil.copy2(MODDIR / "build_all.sh", moddir / "build_all.sh")
        (moddir / "AGENTS.md").write_text("当前10章\n附录八种\n", encoding='utf-8')

        # 创建合订本（10章）
        book = ""
        for i in range(1, 11):
            book += f"### 第{int2cn(i)}章 标题{i}\n\n内容{i}\n\n"
        (Path(tmpdir) / "生命论合订本_最新.md").write_text(book, encoding='utf-8')

        # 创建技能目录
        skill_dir = Path(tmpdir) / "mingben-workbench"
        skill_dir.mkdir()
        shutil.copytree(SCRIPTS, skill_dir / "scripts")
        (skill_dir / "SKILL.md").write_text("# 技能\n全本10章\n附录八种\n", encoding='utf-8')
        for ref in ['epistemology.md', 'growth.md', 'quality.md', 'output.md',
                    'writing.md', 'monitor.md', 'feishu.md', 'app.md', 'concepts.md', 'mingxing.md']:
            (skill_dir / ref).write_text(f"# {ref}\n", encoding='utf-8')

        # backup.sh
        (Path(tmpdir) / "backup.sh").write_text("#!/bin/bash\nfor skill in mingben-workbench; do echo $skill; done\n闪光点.md 创作日志.md 生命论合订本_最新.md\n", encoding='utf-8')

        # 修改self_audit.py的路径锚定指向临时目录
        audit_src = (SCRIPTS / "self_audit.py").read_text(encoding='utf-8')
        audit_src = audit_src.replace(
            'SCRIPT_DIR = Path(__file__).parent',
            f'SCRIPT_DIR = Path(r"{scripts_dst}")'
        ).replace(
            'SKILL_DIR = SCRIPT_DIR.parent',
            f'SKILL_DIR = Path(r"{skill_dir}")'
        ).replace(
            'WORKSPACE = SKILL_DIR.parent',
            f'WORKSPACE = Path(r"{tmpdir}")'
        ).replace(
            'MODDIR = WORKSPACE / "生命论_模块化"',
            f'MODDIR = Path(r"{moddir}")'
        ).replace(
            'FULL_MD = WORKSPACE / "生命论合订本_最新.md"',
            f'FULL_MD = Path(r"{tmpdir}/生命论合订本_最新.md")'
        )
        audit_test = scripts_dst / "self_audit_test.py"
        audit_test.write_text(audit_src, encoding='utf-8')

        def run_audit():
            env = os.environ.copy()
            env['MINGBEN_SKIP_TESTS'] = '1'
            r = subprocess.run([sys.executable, str(audit_test), '--quiet'],
                             capture_output=True, text=True, timeout=30, env=env)
            return r

        # 3a. 干净状态应该通过
        r = run_audit()
        if r.returncode == 0:
            ok("干净状态自筛通过")
        else:
            fail(f"干净状态自筛失败:\n{r.stdout}")

        # 3b. 注入错误章数
        (skill_dir / "SKILL.md").write_text("# 技能\n全本999章\n附录八种\n", encoding='utf-8')
        r = run_audit()
        if r.returncode != 0 and "章数不一致" in r.stdout:
            ok("注入错误章数→被抓出")
        else:
            fail(f"错误章数未被抓出:\n{r.stdout}")
        # 恢复
        (skill_dir / "SKILL.md").write_text("# 技能\n全本10章\n附录八种\n", encoding='utf-8')

        # 3c. 注入失效引用
        (skill_dir / "SKILL.md").write_text("# 技能\n全本10章\n附录八种\n\n`python3 scripts/nonexistent.py`\n", encoding='utf-8')
        r = run_audit()
        if r.returncode != 0 and "失效引用" in r.stdout:
            ok("注入失效引用→被抓出")
        else:
            fail(f"失效引用未被抓出:\n{r.stdout}")
        (skill_dir / "SKILL.md").write_text("# 技能\n全本10章\n附录八种\n", encoding='utf-8')

        # 3d. 注入交叉引用越界
        (Path(tmpdir) / "生命论合订本_最新.md").write_text(
            book + "### 第十一章 越界章\n\n参见第九十九章。\n", encoding='utf-8')
        r = run_audit()
        if r.returncode != 0 and "交叉引用" in r.stdout:
            ok("注入交叉引用越界→被抓出")
        else:
            fail(f"交叉引用越界未被抓出:\n{r.stdout}")
        (Path(tmpdir) / "生命论合订本_最新.md").write_text(book, encoding='utf-8')

        # 3e. 注入过时关键词
        (skill_dir / "SKILL.md").write_text("# 技能\n全本10章\n附录八种\n请访问shengminglun.git\n", encoding='utf-8')
        r = run_audit()
        if r.returncode != 0 and "过时关键词" in r.stdout:
            ok("注入过时关键词→被抓出")
        else:
            fail(f"过时关键词未被抓出:\n{r.stdout}")
        (skill_dir / "SKILL.md").write_text("# 技能\n全本10章\n附录八种\n", encoding='utf-8')

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ========== 测试4: build.sh 质检抓bug能力 ==========

def test_build_quality_check():
    section("测试4: build.sh 质检抓bug能力")

    tmpdir = tempfile.mkdtemp(prefix="mingben_build_")
    try:
        moddir = Path(tmpdir) / "生命论_模块化"
        moddir.mkdir()

        # 创建正确的10章
        def make_book(n):
            return ''.join(f"### 第{int2cn(i)}章 标题{i}\n\n内容{i}\n\n" for i in range(1, n+1))

        (moddir / "00_总序与导论.md").write_text("# 导论\n\n", encoding='utf-8')
        (moddir / "manifest.txt").write_text("", encoding='utf-8')

        # 复制build.sh
        build_src = (MODDIR / "build.sh").read_text(encoding='utf-8')
        (moddir / "build.sh").write_text(build_src, encoding='utf-8')
        (Path(tmpdir) / "publish_style.tex").write_text("", encoding='utf-8')
        (Path(tmpdir) / "html_header.html").write_text("<style></style>", encoding='utf-8')

        def run_check(book_text):
            (Path(tmpdir) / "生命论合订本_最新.md").write_text(book_text, encoding='utf-8')
            r = subprocess.run(['bash', str(moddir / "build.sh"), '--check'],
                             capture_output=True, text=True, cwd=str(tmpdir), timeout=30)
            return r

        # 4a. 正确内容通过
        r = run_check(make_book(10))
        if r.returncode == 0:
            ok("正确10章质检通过")
        else:
            fail(f"正确内容质检失败:\n{r.stdout}\n{r.stderr}")

        # 4b. 编号重复
        bad_book = make_book(10).replace("### 第三章 标题3", "### 第二章 标题3")
        r = run_check(bad_book)
        if r.returncode != 0 and "重复" in r.stdout:
            ok("编号重复→被抓出")
        else:
            fail(f"编号重复未被抓出:\n{r.stdout}")

        # 4c. 编号跳跃
        bad_book = make_book(10).replace("### 第三章 标题3", "### 第五章 标题3")
        r = run_check(bad_book)
        if r.returncode != 0 and "不连续" in r.stdout:
            ok("编号跳跃→被抓出")
        else:
            fail(f"编号跳跃未被抓出:\n{r.stdout}")

        # 4d. 标题重复
        bad_book = make_book(10).replace("### 第五章 标题5", "### 第五章 标题3")
        r = run_check(bad_book)
        if r.returncode != 0 and "标题重复" in r.stdout:
            ok("标题重复→被抓出")
        else:
            fail(f"标题重复未被抓出:\n{r.stdout}")

        # 4e. null字节
        bad_book = make_book(10).replace("内容5", "内容\x005")
        r = run_check(bad_book)
        if r.returncode != 0 and "null" in r.stdout.lower():
            ok("null字节→被抓出")
        else:
            fail(f"null字节未被抓出:\n{r.stdout}")

        # 4f. 未知参数被拒绝
        r = subprocess.run(['bash', str(moddir / "build.sh"), "--typo"],
                         capture_output=True, text=True, cwd=str(tmpdir), timeout=10)
        if r.returncode != 0 and "未知参数" in r.stdout:
            ok("未知参数→被拒绝")
        else:
            fail(f"未知参数未被拒绝:\n{r.stdout}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ========== 测试5: replace.sh --add 插入顺序 ==========

def test_replace_add_order():
    section("测试5: replace.sh --add manifest插入顺序")

    tmpdir = tempfile.mkdtemp(prefix="mingben_replace_")
    try:
        moddir = Path(tmpdir) / "生命论_模块化"
        moddir.mkdir()

        # 创建3个卷
        for juan in range(1, 4):
            (moddir / f"{juan:02d}_卷{juan}").mkdir()
        manifest = "01_卷1/篇一.md\n02_卷2/篇一.md\n03_卷3/篇一.md\n"
        (moddir / "manifest.txt").write_text(manifest, encoding='utf-8')
        for juan in range(1, 4):
            (moddir / f"{juan:02d}_卷{juan}" / "篇一.md").write_text(f"# 卷{juan}\n", encoding='utf-8')

        # 复制replace.sh到模块化目录内（脚本以自身位置定位MODDIR）
        replace_src = (MODDIR / "replace.sh").read_text(encoding='utf-8')
        (moddir / "replace.sh").write_text(replace_src, encoding='utf-8')

        # 在卷2添加新文件
        new_file = Path(tmpdir) / "新篇.md"
        new_file.write_text("## 新篇\n\n内容\n", encoding='utf-8')

        r = subprocess.run(['bash', str(moddir / "replace.sh"), '--add', '02_卷2', str(new_file)],
                         capture_output=True, text=True, cwd=str(tmpdir), timeout=10)

        result = (moddir / "manifest.txt").read_text(encoding='utf-8')
        lines = [l.strip() for l in result.splitlines() if l.strip()]

        # 验证新文件在卷2区域（在卷1之后、卷3之前）
        try:
            idx_new = lines.index('02_卷2/新篇.md')
            idx_v3 = lines.index('03_卷3/篇一.md')
            idx_v1 = lines.index('01_卷1/篇一.md')
            if idx_v1 < idx_new < idx_v3:
                ok("新文件正确插入到卷2区域（非末尾追加）")
            else:
                fail(f"插入顺序错误: {lines}")
        except ValueError as e:
            fail(f"manifest内容异常: {lines}, 错误: {e}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ========== 主入口 ==========

if __name__ == '__main__':
    print("=" * 50)
    print("  明本系统测试套件 — 实际执行验证")
    print("=" * 50)

    test_number_conversion()
    test_auto_merge()
    test_auto_merge_cross_module_refs()
    test_self_audit_detection()
    test_build_quality_check()
    test_replace_add_order()

    print(f"\n{'='*50}")
    print(f"  结果: ✅{passed}通过  ❌{failed}失败")
    print(f"{'='*50}")

    sys.exit(1 if failed > 0 else 0)
