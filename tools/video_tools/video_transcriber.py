#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用视频文案提取工具 v2.0（融合版）
支持：抖音、B站
B站策略：CC字幕(几秒) > yt-dlp下载音频+faster-whisper转写
抖音策略：B站搜索相同视频找CC字幕 > 下载+whisper转写
功能：批量处理、--subtitles-only、模型选择、三种输出格式(纯文本/时间戳/JSON)、繁体转简体

用法：
  python3 video_transcriber.py <视频URL或BV号>
  python3 video_transcriber.py --batch urls.txt
  python3 video_transcriber.py <URL> --output my_output --model medium
  python3 video_transcriber.py <URL> --subtitles-only
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path

# ============================================================
# 配置
# ============================================================
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

# ============================================================
# 依赖管理
# ============================================================
def ensure_requests():
    try:
        import requests
        return requests
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
        import requests
        return requests

def ensure_whisper():
    try:
        from faster_whisper import WhisperModel
        return WhisperModel
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "faster-whisper", "-q"])
        from faster_whisper import WhisperModel
        return WhisperModel

def ensure_opencc():
    try:
        from opencc import OpenCC
        return OpenCC
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencc-python-reimplemented", "-q"])
        from opencc import OpenCC
        return OpenCC

# ============================================================
# 工具函数
# ============================================================
def run_cmd(cmd, timeout=120):
    """运行shell命令"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", -1

def t2s(text):
    """繁体转简体"""
    OpenCC = ensure_opencc()
    cc = OpenCC('t2s')
    return cc.convert(text)

def format_timestamp(seconds):
    """秒数转 MM:SS 格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

# ============================================================
# B站API
# ============================================================
def extract_bvid(url_or_bvid):
    """从URL或文本中提取BV号"""
    if re.match(r'^BV[a-zA-Z0-9]+$', url_or_bvid):
        return url_or_bvid
    match = re.search(r'(BV[a-zA-Z0-9]+)', url_or_bvid)
    return match.group(1) if match else None

def get_bilibili_video_info(bvid):
    """获取B站视频信息（标题、cid、时长）"""
    requests = ensure_requests()
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取视频信息失败: {data.get('message')}")
    return data["data"]

def get_bilibili_subtitle_list(bvid, cid):
    """获取B站视频的字幕列表"""
    requests = ensure_requests()
    url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        return []
    return data.get("data", {}).get("subtitle", {}).get("subtitles", [])

def download_bilibili_subtitle(subtitle_url):
    """下载B站字幕内容"""
    requests = ensure_requests()
    if subtitle_url.startswith("//"):
        subtitle_url = "https:" + subtitle_url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    }
    resp = requests.get(subtitle_url, headers=headers, timeout=10)
    return resp.json()

def parse_subtitle_json(subtitle_data):
    """解析B站字幕JSON，返回segments列表"""
    results = []
    for item in subtitle_data.get("body", []):
        results.append({
            "start": round(item.get("from", 0), 2),
            "end": round(item.get("to", 0), 2),
            "text": item.get("content", "")
        })
    return results

def search_bilibili(keyword):
    """在B站搜索关键词，返回视频列表"""
    requests = ensure_requests()
    url = f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={urllib.parse.quote(keyword)}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        if data.get('code') == 0:
            return data['data'].get('result', [])[:5]
    except Exception as e:
        print(f"[!] B站搜索失败: {e}", file=sys.stderr)
    return []

# ============================================================
# 抖音
# ============================================================
def resolve_douyin_short_link(url):
    """解析抖音短链接，返回视频ID"""
    out, err, rc = run_cmd(f'curl -sL -o /dev/null -w "%{{url_effective}}" "{url}"')
    if rc == 0 and out:
        m = re.search(r'/video/(\d+)', out)
        if m:
            return m.group(1)
    return None

def get_douyin_video_info(video_id):
    """用playwright获取抖音视频信息"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] playwright未安装，抖音视频需手动提供标题/描述", file=sys.stderr)
        return {'title': f'抖音_{video_id}', 'desc': '', 'video_url': ''}

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

        try:
            btn = page.query_selector('text=展开')
            if btn:
                btn.click()
                page.wait_for_timeout(2000)
        except:
            pass

        title = page.title()
        desc = page.evaluate('''() => {
            const meta = document.querySelector('meta[property="og:description"]');
            return meta ? meta.content : '';
        }''')
        video_url = page.evaluate('''() => {
            const video = document.querySelector('video');
            return video ? video.src : '';
        }''')
        browser.close()
        return {'title': title, 'desc': desc, 'video_url': video_url}

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

# ============================================================
# Whisper转写
# ============================================================
def whisper_transcribe(audio_path, model_size="small"):
    """用faster-whisper转写音频"""
    WhisperModel = ensure_whisper()
    print(f"  加载模型: {model_size}...", file=sys.stderr)
    model = WhisperModel(model_size, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
    print(f"  转写中...", file=sys.stderr)
    segments, info = model.transcribe(
        audio_path, language='zh', beam_size=5, vad_filter=True
    )
    print(f"  语言: {info.language}, 时长: {info.duration:.1f}秒", file=sys.stderr)

    results = []
    for seg in segments:
        results.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip()
        })
    return results

# ============================================================
# 音频下载
# ============================================================
def download_bilibili_audio(bvid, output_dir):
    """用yt-dlp下载B站视频音频"""
    url = f"https://www.bilibili.com/video/{bvid}"
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "0",
        "-o", output_template, "--no-playlist", "--quiet", "--no-warnings", url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise Exception(f"yt-dlp下载失败: {result.stderr[:200]}")
    audio_files = list(Path(output_dir).glob(f"{bvid}*.mp3")) or list(Path(output_dir).glob("*.mp3"))
    if not audio_files:
        raise Exception("未找到下载的音频文件")
    return str(audio_files[0])

# ============================================================
# 格式化输出
# ============================================================
def format_plain_text(segments):
    return "\n".join([s["text"] for s in segments])

def format_with_timestamps(segments):
    lines = []
    for s in segments:
        time_str = f"[{format_timestamp(s['start'])} - {format_timestamp(s['end'])}]"
        lines.append(f"{time_str} {s['text']}")
    return "\n".join(lines)

def format_json(segments, title, bvid="", duration=0, source=""):
    return json.dumps({
        "title": title, "bvid": bvid, "duration": duration,
        "source": source, "segments": segments
    }, ensure_ascii=False, indent=2)

def save_results(segments, title, output_dir, bvid="", duration=0, source=""):
    """保存三种格式的结果"""
    os.makedirs(output_dir, exist_ok=True)
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)[:50]
    base_name = f"{bvid}_{safe_title}" if bvid else safe_title

    # 繁体转简体
    for s in segments:
        s["text"] = t2s(s["text"])

    txt_path = os.path.join(output_dir, f"{base_name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(format_plain_text(segments))

    srt_path = os.path.join(output_dir, f"{base_name}_时间戳.txt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(format_with_timestamps(segments))

    json_path = os.path.join(output_dir, f"{base_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(format_json(segments, title, bvid, duration, source))

    print(f"  纯文本: {txt_path}", file=sys.stderr)
    print(f"  时间戳: {srt_path}", file=sys.stderr)
    print(f"  JSON: {json_path}", file=sys.stderr)
    return [txt_path, srt_path, json_path]

# ============================================================
# 主流程：B站
# ============================================================
def process_bilibili(url_or_bvid, output_dir="output", subtitles_only=False, model_size="small"):
    """处理B站视频"""
    bvid = extract_bvid(url_or_bvid)
    if not bvid:
        raise Exception(f"无法提取BV号: {url_or_bvid}")

    print(f"处理B站视频: {bvid}", file=sys.stderr)
    video_info = get_bilibili_video_info(bvid)
    title = video_info.get("title", "未知标题")
    cid = video_info.get("cid")
    duration = video_info.get("duration", 0)
    print(f"  标题: {title}", file=sys.stderr)
    print(f"  时长: {duration}秒", file=sys.stderr)

    subtitles = get_bilibili_subtitle_list(bvid, cid)
    has_subtitles = len(subtitles) > 0
    print(f"  CC字幕: {'有' if has_subtitles else '无'}", file=sys.stderr)

    segments = []
    source = ""

    if has_subtitles:
        print(f"  提取CC字幕...", file=sys.stderr)
        sub_data = download_bilibili_subtitle(subtitles[0]["subtitle_url"])
        segments = parse_subtitle_json(sub_data)
        source = "cc_subtitle"
        print(f"  字幕提取完成: {len(segments)}段", file=sys.stderr)
    elif subtitles_only:
        print(f"  无CC字幕，--subtitles-only指定，跳过", file=sys.stderr)
        return None
    else:
        print(f"  无CC字幕，yt-dlp下载音频并转写...", file=sys.stderr)
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = download_bilibili_audio(bvid, tmpdir)
            segments = whisper_transcribe(audio_path, model_size)
            source = "whisper_transcription"
        print(f"  转写完成: {len(segments)}段", file=sys.stderr)

    files = save_results(segments, title, output_dir, bvid, duration, source)
    return {"bvid": bvid, "title": title, "source": source,
            "segments_count": len(segments), "files": files}

# ============================================================
# 主流程：抖音
# ============================================================
def process_douyin(url, output_dir="output", model_size="small"):
    """处理抖音视频"""
    print("[*] 解析抖音链接...", file=sys.stderr)
    video_id = resolve_douyin_short_link(url)
    if not video_id:
        raise Exception("无法解析抖音链接")
    print(f"  视频ID: {video_id}", file=sys.stderr)

    info = get_douyin_video_info(video_id)
    title = info['title']
    desc = info['desc']
    video_url = info['video_url']
    print(f"  标题: {title}", file=sys.stderr)

    # 策略1：在B站搜索相同视频找CC字幕
    print("[*] 尝试在B站搜索相同视频...", file=sys.stderr)
    search_keyword = desc[:30] if desc else title[:30]
    results = search_bilibili(search_keyword)
    for r in results:
        bvid = r.get('bvid', '')
        r_title = r.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
        print(f"  - 找到: {r_title[:50]} ({bvid})", file=sys.stderr)
        try:
            vinfo = get_bilibili_video_info(bvid)
            subs = get_bilibili_subtitle_list(bvid, vinfo.get('cid'))
            if subs:
                print("[√] 找到B站CC字幕，直接使用！", file=sys.stderr)
                sub_data = download_bilibili_subtitle(subs[0]["subtitle_url"])
                segments = parse_subtitle_json(sub_data)
                files = save_results(segments, title, output_dir, bvid, vinfo.get('duration', 0), "bilibili_cc_subtitle")
                return {"bvid": bvid, "title": title, "source": "bilibili_cc_subtitle",
                        "segments_count": len(segments), "files": files}
        except Exception as e:
            print(f"  跳过: {e}", file=sys.stderr)

    # 策略2：下载抖音视频音频转写
    if not video_url:
        raise Exception("无法获取抖音视频URL，且B站未找到相同视频")

    print("[*] B站无相同视频，下载抖音音频转写...", file=sys.stderr)
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, f'{video_id}.mp4')
        audio_path = os.path.join(tmpdir, f'{video_id}.wav')
        download_file(video_url, video_path)
        run_cmd(f'ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {audio_path} -y')
        if not os.path.exists(audio_path):
            raise Exception("音频提取失败")
        segments = whisper_transcribe(audio_path, model_size)

    files = save_results(segments, title, output_dir, source="douyin_whisper")
    return {"video_id": video_id, "title": title, "source": "douyin_whisper",
            "segments_count": len(segments), "files": files}

# ============================================================
# 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="通用视频文案提取工具 v2.0（抖音+B站）")
    parser.add_argument("url", nargs="?", help="视频URL或BV号")
    parser.add_argument("--batch", help="批量处理文件（每行一个URL）")
    parser.add_argument("--output", default="output", help="输出目录（默认: output）")
    parser.add_argument("--subtitles-only", action="store_true", help="只提取CC字幕，无字幕则跳过")
    parser.add_argument("--model", default="small",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper模型大小（默认: small）")
    args = parser.parse_args()

    if not args.url and not args.batch:
        parser.print_help()
        sys.exit(1)

    urls = []
    if args.url:
        urls.append(args.url)
    if args.batch:
        with open(args.batch, "r", encoding="utf-8") as f:
            urls.extend([line.strip() for line in f if line.strip()])

    print(f"共 {len(urls)} 个视频待处理", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}]", file=sys.stderr)
        try:
            if 'douyin.com' in url:
                result = process_douyin(url, args.output, args.model)
            elif 'bilibili.com' in url or 'b23.tv' in url or re.match(r'^BV[a-zA-Z0-9]+$', url):
                result = process_bilibili(url, args.output, args.subtitles_only, args.model)
            else:
                print(f"  [!] 不支持的平台: {url}", file=sys.stderr)
                result = {"url": url, "error": "不支持的平台"}
            if result:
                results.append(result)
        except Exception as e:
            print(f"  错误: {e}", file=sys.stderr)
            results.append({"url": url, "error": str(e)})

    print("\n" + "=" * 50, file=sys.stderr)
    success = sum(1 for r in results if "error" not in r)
    print(f"处理完成: {len(results)} 个视频, 成功: {success}, 失败: {len(results) - success}", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
