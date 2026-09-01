#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频文案高效提取工具 v1.0

功能：
1. 自动检测CC字幕，有就直接提取（几秒完成）
2. 没有字幕就下载音频 + faster-whisper转写（比openai-whisper快4倍）
3. 支持批量处理
4. 输出：纯文本、带时间戳、JSON

用法：
  python3 bilibili_transcriber.py <B站URL或BV号>
  python3 bilibili_transcriber.py --batch urls.txt
  python3 bilibili_transcriber.py --subtitles-only <URL>  # 只提取字幕，不转写
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

try:
    from faster_whisper import WhisperModel
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "faster-whisper", "-q"])
    from faster_whisper import WhisperModel


# ============================================================
# B站API工具
# ============================================================

def extract_bvid(url_or_bvid):
    """从URL或文本中提取BV号"""
    # 直接是BV号
    if re.match(r'^BV[a-zA-Z0-9]+$', url_or_bvid):
        return url_or_bvid
    # 从URL中提取
    match = re.search(r'(BV[a-zA-Z0-9]+)', url_or_bvid)
    if match:
        return match.group(1)
    return None


def get_video_info(bvid):
    """获取视频信息（标题、分P、字幕列表）"""
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


def get_subtitle_list(bvid, cid):
    """获取视频的字幕列表"""
    url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        return []
    subtitles = data.get("data", {}).get("subtitle", {}).get("subtitles", [])
    return subtitles


def download_subtitle(subtitle_url):
    """下载字幕内容"""
    if subtitle_url.startswith("//"):
        subtitle_url = "https:" + subtitle_url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    }
    resp = requests.get(subtitle_url, headers=headers, timeout=10)
    return resp.json()


def parse_subtitle_json(subtitle_data):
    """解析B站字幕JSON，返回带时间戳的文本"""
    results = []
    for item in subtitle_data.get("body", []):
        start = item.get("from", 0)
        end = item.get("to", 0)
        content = item.get("content", "")
        results.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "text": content
        })
    return results


# ============================================================
# 音频下载与转写
# ============================================================

def download_audio(bvid, output_dir):
    """用yt-dlp下载视频音频"""
    url = f"https://www.bilibili.com/video/{bvid}"
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "-x",  # 只提取音频
        "--audio-format", "mp3",
        "--audio-quality", "0",  # 最佳质量
        "-o", output_template,
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise Exception(f"下载音频失败: {result.stderr}")
    
    # 找到下载的文件
    audio_files = list(Path(output_dir).glob(f"{bvid}*.mp3"))
    if not audio_files:
        audio_files = list(Path(output_dir).glob("*.mp3"))
    if not audio_files:
        raise Exception("未找到下载的音频文件")
    
    return str(audio_files[0])


def transcribe_audio(audio_path, model_size="small", language="zh"):
    """用faster-whisper转写音频"""
    print(f"  加载模型: {model_size}...", file=sys.stderr)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print(f"  转写中...", file=sys.stderr)
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True  # 语音活动检测，跳过静音
    )
    
    results = []
    for segment in segments:
        results.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })
    
    return results


# ============================================================
# 格式化输出
# ============================================================

def format_timestamp(seconds):
    """秒数转 MM:SS 格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_plain_text(segments):
    """纯文本格式"""
    return "\n".join([s["text"] for s in segments])


def format_with_timestamps(segments):
    """带时间戳格式"""
    lines = []
    for s in segments:
        time_str = f"[{format_timestamp(s['start'])} - {format_timestamp(s['end'])}]"
        lines.append(f"{time_str} {s['text']}")
    return "\n".join(lines)


def format_json(segments, video_info):
    """JSON格式"""
    return json.dumps({
        "title": video_info.get("title", ""),
        "bvid": video_info.get("bvid", ""),
        "duration": video_info.get("duration", 0),
        "segments": segments
    }, ensure_ascii=False, indent=2)


# ============================================================
# 主流程
# ============================================================

def process_video(url_or_bvid, output_dir="output", subtitles_only=False, model_size="small"):
    """处理单个视频"""
    bvid = extract_bvid(url_or_bvid)
    if not bvid:
        raise Exception(f"无法提取BV号: {url_or_bvid}")
    
    print(f"处理视频: {bvid}", file=sys.stderr)
    
    # 获取视频信息
    video_info = get_video_info(bvid)
    title = video_info.get("title", "未知标题")
    cid = video_info.get("cid")
    duration = video_info.get("duration", 0)
    print(f"  标题: {title}", file=sys.stderr)
    print(f"  时长: {duration}秒", file=sys.stderr)
    
    # 检查是否有字幕
    subtitles = get_subtitle_list(bvid, cid)
    has_subtitles = len(subtitles) > 0
    print(f"  CC字幕: {'有' if has_subtitles else '无'}", file=sys.stderr)
    
    segments = []
    source = ""
    
    if has_subtitles:
        # 优先用CC字幕
        print(f"  提取CC字幕...", file=sys.stderr)
        sub = subtitles[0]  # 取第一个字幕
        sub_data = download_subtitle(sub["subtitle_url"])
        segments = parse_subtitle_json(sub_data)
        source = "cc_subtitle"
        print(f"  字幕提取完成: {len(segments)}段", file=sys.stderr)
    elif subtitles_only:
        print(f"  无CC字幕，且指定了--subtitles-only，跳过", file=sys.stderr)
        return None
    else:
        # 没有字幕，下载音频转写
        print(f"  无CC字幕，下载音频并转写...", file=sys.stderr)
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = download_audio(bvid, tmpdir)
            print(f"  音频下载完成: {audio_path}", file=sys.stderr)
            segments = transcribe_audio(audio_path, model_size=model_size)
            source = "whisper_transcription"
        print(f"  转写完成: {len(segments)}段", file=sys.stderr)
    
    # 保存结果
    os.makedirs(output_dir, exist_ok=True)
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)[:50]
    base_name = f"{bvid}_{safe_title}"
    
    # 纯文本
    txt_path = os.path.join(output_dir, f"{base_name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(format_plain_text(segments))
    
    # 带时间戳
    srt_path = os.path.join(output_dir, f"{base_name}_时间戳.txt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(format_with_timestamps(segments))
    
    # JSON
    json_path = os.path.join(output_dir, f"{base_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(format_json(segments, video_info))
    
    print(f"  输出文件:", file=sys.stderr)
    print(f"    纯文本: {txt_path}", file=sys.stderr)
    print(f"    时间戳: {srt_path}", file=sys.stderr)
    print(f"    JSON: {json_path}", file=sys.stderr)
    
    return {
        "bvid": bvid,
        "title": title,
        "source": source,
        "segments_count": len(segments),
        "files": [txt_path, srt_path, json_path]
    }


def main():
    parser = argparse.ArgumentParser(description="B站视频文案高效提取工具")
    parser.add_argument("url", nargs="?", help="B站视频URL或BV号")
    parser.add_argument("--batch", help="批量处理，包含URL列表的文本文件（每行一个）")
    parser.add_argument("--output", default="output", help="输出目录（默认: output）")
    parser.add_argument("--subtitles-only", action="store_true", help="只提取CC字幕，无字幕则跳过")
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large"], 
                        help="Whisper模型大小（默认: small，越大越准越慢）")
    
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
            result = process_video(url, args.output, args.subtitles_only, args.model)
            if result:
                results.append(result)
        except Exception as e:
            print(f"  错误: {e}", file=sys.stderr)
            results.append({"url": url, "error": str(e)})
    
    print("\n" + "=" * 50, file=sys.stderr)
    print(f"处理完成: {len(results)} 个视频", file=sys.stderr)
    success = sum(1 for r in results if "error" not in r)
    print(f"成功: {success}, 失败: {len(results) - success}", file=sys.stderr)
    
    # 输出结果摘要
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
