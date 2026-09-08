#!/usr/bin/env python3
"""
通用视频文案提取工具 v1.0
支持：抖音、B站
优先级：B站CC字幕(几秒) > 抖音下载+whisper转写(几分钟)
用法：python3 video_transcriber.py <视频链接> [输出目录]
"""

import sys
import os
import re
import json
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

# ============================================================
# 配置
# ============================================================
WHISPER_MODEL = "small"  # tiny/base/small/medium/large
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

# ============================================================
# 工具函数
# ============================================================
def run_cmd(cmd, timeout=120):
    """运行shell命令，返回(stdout, stderr, returncode)"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", -1

def download_file(url, path, headers=None):
    """下载文件"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Referer': 'https://www.douyin.com/'
        }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        with open(path, 'wb') as f:
            f.write(resp.read())
    return path

def resolve_douyin_short_link(url):
    """解析抖音短链接，返回视频ID"""
    out, err, rc = run_cmd(f'curl -sL -o /dev/null -w "%{{url_effective}}" "{url}"')
    if rc == 0 and out:
        m = re.search(r'/video/(\d+)', out)
        if m:
            return m.group(1)
    return None

def get_douyin_video_info(video_id):
    """用playwright获取抖音视频信息（标题、描述、视频URL）"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] playwright未安装，尝试用curl获取...")
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path='/usr/local/bin/chromium',
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            viewport={'width': 390, 'height': 844}
        )
        page = context.new_page()
        page.goto(f'https://www.douyin.com/video/{video_id}', timeout=30000)
        page.wait_for_timeout(5000)

        # 点击展开
        try:
            btn = page.query_selector('text=展开')
            if btn:
                btn.click()
                page.wait_for_timeout(2000)
        except:
            pass

        title = page.title()
        desc = page.evaluate('''() => {
            const all = document.body.innerText;
            const idx = all.indexOf('逢高');
            if (idx >= 0) return all.substring(idx, idx + 300);
            // 尝试其他方式
            const meta = document.querySelector('meta[property="og:description"]');
            return meta ? meta.content : '';
        }''')

        video_url = page.evaluate('''() => {
            const video = document.querySelector('video');
            if (video) return video.src;
            return '';
        }''')

        browser.close()
        return {'title': title, 'desc': desc, 'video_url': video_url}

def search_bilibili(keyword):
    """在B站搜索关键词，返回视频列表"""
    url = f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={urllib.parse.quote(keyword)}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get('code') == 0:
                return data['data'].get('result', [])[:5]
    except Exception as e:
        print(f"[!] B站搜索失败: {e}")
    return []

def get_bilibili_cc_subtitle(bvid):
    """获取B站CC字幕"""
    # 先获取视频信息（cid和aid）
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get('code') != 0:
                return None
            cid = data['data']['cid']
            aid = data['data']['aid']
    except Exception as e:
        print(f"[!] 获取B站视频信息失败: {e}")
        return None

    # 获取字幕列表
    url2 = f'https://api.bilibili.com/x/player/v2?aid={aid}&cid={cid}'
    try:
        req = urllib.request.Request(url2, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            subtitles = data.get('data', {}).get('subtitle', {}).get('subtitles', [])
            if not subtitles:
                return None
            # 取第一个字幕（通常是中文）
            sub_url = 'https:' + subtitles[0]['subtitle_url']
            req2 = urllib.request.Request(sub_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                sub_data = json.loads(resp2.read())
                lines = []
                for item in sub_data.get('body', []):
                    start = item['from']
                    end = item['to']
                    text = item['content']
                    lines.append(f'[{start:.1f}s - {end:.1f}s] {text}')
                return lines
    except Exception as e:
        print(f"[!] 获取B站字幕失败: {e}")
    return None

def extract_bvid_from_url(url):
    """从B站URL提取bvid"""
    m = re.search(r'BV[a-zA-Z0-9]+', url)
    return m.group(0) if m else None

def whisper_transcribe(audio_path):
    """用faster-whisper转写音频"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[!] 安装faster-whisper...")
        run_cmd('pip3 install faster-whisper -q')
        from faster_whisper import WhisperModel

    print(f"[*] 加载whisper模型({WHISPER_MODEL})...")
    model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)

    print("[*] 转写中...")
    segments, info = model.transcribe(audio_path, language='zh', beam_size=5)
    print(f"[*] 语言: {info.language}, 时长: {info.duration:.1f}秒")

    lines = []
    full_text = []
    for seg in segments:
        lines.append(f'[{seg.start:.1f}s - {seg.end:.1f}s] {seg.text}')
        full_text.append(seg.text)

    return lines, ''.join(full_text)

def t2s(text):
    """繁体转简体"""
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')
        return cc.convert(text)
    except ImportError:
        run_cmd('pip3 install opencc-python-reimplemented -q')
        from opencc import OpenCC
        cc = OpenCC('t2s')
        return cc.convert(text)

def save_result(title, desc, lines, full_text, output_dir, source=''):
    """保存结果"""
    os.makedirs(output_dir, exist_ok=True)
    # 清理文件名
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)[:50]
    filepath = os.path.join(output_dir, f'{safe_title}_文案.txt')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'标题：{title}\n')
        f.write(f'描述：{desc}\n')
        f.write(f'来源：{source}\n')
        f.write('=' * 60 + '\n\n')
        f.write('【带时间轴版本】\n\n')
        f.write('\n'.join(lines))
        f.write('\n\n' + '=' * 60 + '\n\n')
        f.write('【纯文本版本】\n\n')
        f.write(full_text)

    print(f"[√] 已保存: {filepath}")
    return filepath

# ============================================================
# 主流程
# ============================================================
def transcribe_douyin(url, output_dir):
    """抖音视频文案提取"""
    print("[*] 解析抖音链接...")
    video_id = resolve_douyin_short_link(url)
    if not video_id:
        print("[!] 无法解析抖音链接")
        return None

    print(f"[*] 视频ID: {video_id}")

    # 获取视频信息
    info = get_douyin_video_info(video_id)
    if not info:
        print("[!] 无法获取视频信息")
        return None

    title = info['title']
    desc = info['desc']
    video_url = info['video_url']

    print(f"[*] 标题: {title}")
    print(f"[*] 描述: {desc[:100]}...")

    # 策略1：在B站搜索相同视频，看有没有CC字幕
    print("[*] 尝试在B站搜索相同视频...")
    search_keyword = desc[:30] if desc else title[:30]
    results = search_bilibili(search_keyword)
    for r in results:
        bvid = r.get('bvid', '')
        r_title = r.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
        print(f"  - 找到: {r_title[:50]} ({bvid})")
        subtitles = get_bilibili_cc_subtitle(bvid)
        if subtitles:
            print("[√] 找到B站CC字幕，直接使用！")
            full_text = ''.join([re.sub(r'\[.*?\] ', '', l) for l in subtitles])
            return save_result(title, desc, subtitles, full_text, output_dir, source='B站CC字幕')

    print("[*] B站无相同视频或无字幕，走抖音下载+转写路线")

    # 策略2：下载视频音频，whisper转写
    if not video_url:
        print("[!] 无法获取视频URL")
        return None

    video_path = os.path.join(output_dir, f'{video_id}.mp4')
    audio_path = os.path.join(output_dir, f'{video_id}.wav')

    print("[*] 下载视频...")
    try:
        download_file(video_url, video_path)
    except Exception as e:
        print(f"[!] 下载失败: {e}")
        return None

    print("[*] 提取音频...")
    run_cmd(f'ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {audio_path} -y')

    if not os.path.exists(audio_path):
        print("[!] 音频提取失败")
        return None

    # 转写
    lines, full_text = whisper_transcribe(audio_path)

    # 繁体转简体
    lines = [t2s(l) for l in lines]
    full_text = t2s(full_text)

    # 清理临时文件
    os.remove(video_path)
    os.remove(audio_path)

    return save_result(title, desc, lines, full_text, output_dir, source='抖音音频转写')

def transcribe_bilibili(url, output_dir):
    """B站视频文案提取"""
    bvid = extract_bvid_from_url(url)
    if not bvid:
        print("[!] 无法提取bvid")
        return None

    print(f"[*] B站视频: {bvid}")

    # 优先CC字幕
    print("[*] 尝试获取CC字幕...")
    subtitles = get_bilibili_cc_subtitle(bvid)
    if subtitles:
        print("[√] 获取到CC字幕！")
        # 获取标题
        title = f'B站_{bvid}'
        try:
            url2 = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/'}
            req = urllib.request.Request(url2, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                title = data['data']['title']
        except:
            pass

        full_text = ''.join([re.sub(r'\[.*?\] ', '', l) for l in subtitles])
        return save_result(title, '', subtitles, full_text, output_dir, source='B站CC字幕')

    print("[*] 无CC字幕，需要下载音频转写（B站下载较复杂，建议用yt-dlp）")
    # TODO: B站无字幕时的下载转写
    return None

def main():
    if len(sys.argv) < 2:
        print("用法: python3 video_transcriber.py <视频链接> [输出目录]")
        print("支持: 抖音(v.douyin.com / www.douyin.com/video/xxx)")
        print("      B站(bilibili.com/video/BVxxx)")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './video_output'

    print(f"[*] 目标: {url}")
    print(f"[*] 输出目录: {output_dir}")
    print()

    if 'douyin.com' in url:
        result = transcribe_douyin(url, output_dir)
    elif 'bilibili.com' in url or 'b23.tv' in url:
        result = transcribe_bilibili(url, output_dir)
    else:
        print("[!] 不支持的平台")
        sys.exit(1)

    if result:
        print(f"\n[√] 完成！文件: {result}")
    else:
        print("\n[!] 提取失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
