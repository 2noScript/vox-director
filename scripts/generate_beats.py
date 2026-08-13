#!/usr/bin/env python3
"""
Generate a canonical beats.json draft from a topic using Atlas Cloud LLM.

Usage:
  python3 scripts/generate_beats.py out/my-topic "A Brief History of Coffee" [--duration 30] [--aspect 9:16] [--theme american-retro]
"""
import argparse
import json
import os
import sys

import atlas_cloud
from styles import THEME_PRESETS

DEFAULT_LLM = "google/gemini-2.5-flash"


def build_system_prompt():
    return """You are the lead director for Vox-style paper-collage videos.
Your task is to take a TOPIC and produce a strictly valid JSON beat map (`beats.json`) following the Vox Director canonical schema.

RULES FOR THE BEAT MAP:
1. Duration & Beat count:
   - 15s -> ~3 beats (70-80 words total VO)
   - 30s -> ~6 beats (70-80 words total VO)
   - 60s -> 10-12 beats (130-150 words total VO)
2. Hook in Beat 1 (<=3s):
   - Beat 1 headline & narration MUST be a bold claim, provocative question, or surprising stat.
3. Every beat MUST have 1 or 2 shots (e.g. shot 'a' WIDE with title=true, shot 'b' CLOSE with title=false).
4. VARY camera_move across adjacent beats: choose from {push_in, pull_out, pan, tilt, parallax, static}. Never repeat camera_move on consecutive beats.
5. Provide rich element_motion per shot describing moving cut-outs, drifting paper, and halftone pulses.

OUTPUT FORMAT:
Return ONLY a raw JSON object (no markdown backticks, no explanatory prose) adhering exactly to this schema:
{
  "project": "<project_name>",
  "topic": "<topic>",
  "language": "en",
  "aspect": "9:16",
  "style": "collage",
  "provider": "atlas_cloud",
  "theme": "american-retro",
  "arc": "timeline",
  "video_model": "google/gemini-omni-flash/image-to-video",
  "image_model": "google/nano-banana-2/text-to-image",
  "image_resolution": "1k",
  "video_resolution": "720p",
  "motion_style": "punchy",
  "constraints": "strict",
  "voice": {
    "voice_id": "leo",
    "language": "en",
    "speed": 1.0
  },
  "music": "short descriptive music prompt for minimax",
  "mix": {
    "music": 0.6,
    "voice": 1.25
  },
  "caption_style": "white",
  "captions": true,
  "watermark": "Made with Atlas Cloud",
  "beats": [
    {
      "id": 1,
      "title_cn": "",
      "title_en": "HEADLINE",
      "bg": "color description",
      "feel": "mood description",
      "hook": "surprising_stat",
      "narration": "Narration text for beat 1...",
      "shots": [
        {
          "id": "a",
          "dur": 5,
          "title": true,
          "shot_size": "WIDE",
          "camera_move": "push_in",
          "scene": "detailed description of layered paper cut-out poster...",
          "element_motion": "detailed description of element motion..."
        }
      ]
    }
  ]
}
"""


def generate_beats(project_dir, topic, duration=30, aspect="9:16", theme="american-retro", model=DEFAULT_LLM):
    os.makedirs(project_dir, exist_ok=True)
    project_name = os.path.basename(project_dir.rstrip("/"))
    bpath = os.path.join(project_dir, "beats.json")

    user_prompt = f"""Target Topic: "{topic}"
Requested Duration: {duration} seconds
Target Aspect Ratio: {aspect}
Target Visual Theme: {theme}
Project Name: {project_name}

Generate the complete canonical beats.json draft."""

    print(f"Generating beat map via LLM ({model})...")
    raw_response = atlas_cloud.chat(
        model=model,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    # Clean markdown code blocks if returned
    text = raw_response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON response from LLM:")
        print(text)
        raise e

    # Ensure project fields align
    doc["project"] = project_name
    doc["topic"] = topic
    doc["aspect"] = aspect
    doc["theme"] = theme

    with open(bpath, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated {len(doc.get('beats', []))} beats -> {bpath}")
    return bpath


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate beats.json from topic via LLM")
    parser.add_argument("project_dir", help="Project output directory (e.g. out/my-topic)")
    parser.add_argument("topic", help="Topic for the video (e.g. 'History of Coffee')")
    parser.add_argument("--duration", type=int, default=30, help="Target duration in seconds (15, 30, 60)")
    parser.add_argument("--aspect", default="9:16", help="Aspect ratio (9:16, 16:9, 1:1, 3:4)")
    parser.add_argument("--theme", default="american-retro", help="Visual theme preset")
    parser.add_argument("--model", default=DEFAULT_LLM, help="Atlas Cloud LLM model")

    args = parser.parse_args()
    generate_beats(args.project_dir, args.topic, duration=args.duration, aspect=args.aspect, theme=args.theme, model=args.model)
