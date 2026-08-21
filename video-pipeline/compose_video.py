"""
건강 팁 숏폼(60초, 9:16) 영상 합성 모듈.
자막/배경/워드마크만 있는 단순한 텍스트 중심 템플릿 — 배경 영상/이미지 소재 없이도 바로 만들 수 있게
설계했다. ImageMagick 의존성을 피하려고 MoviePy TextClip 대신 PIL로 직접 텍스트를 렌더링한다
(my-video-creator의 english_words_short.py와 같은 접근).
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ColorClip, CompositeVideoClip, ImageClip

from tts import Caption

WIDTH, HEIGHT = 1080, 1920

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NanumGothic.ttf")

BG_COLOR = (18, 22, 28)  # 다크 배경
TITLE_COLOR = (255, 255, 255)
CAPTION_COLOR = (255, 255, 255)
ACCENT_COLOR = (255, 160, 80)  # 워드마크/포인트용
CAPTION_SHADOW = (0, 0, 0)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """어절 단위로 줄바꿈해 max_width를 넘지 않는 줄 목록을 만든다."""
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if probe.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _render_text_image(
    text: str,
    font_size: int,
    color: tuple[int, int, int],
    max_width: int,
    align: str = "center",
    shadow: bool = True,
) -> Image.Image:
    """텍스트를 줄바꿈해서 투명 배경 PNG(PIL Image, RGBA)로 렌더링한다."""
    font = _font(font_size)
    lines = _wrap_text(text, font, max_width)

    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    line_height = int(font_size * 1.5)
    line_widths = [probe.textlength(line, font=font) for line in lines]
    img_width = max(int(max(line_widths, default=0)) + 20, 10)
    img_height = line_height * len(lines) + 20

    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        line_w = line_widths[i]
        x = (img_width - line_w) / 2 if align == "center" else 10
        y = 10 + i * line_height
        if shadow:
            draw.text((x + 3, y + 3), line, font=font, fill=(*CAPTION_SHADOW, 200))
        draw.text((x, y), line, font=font, fill=(*color, 255))

    return img


def _image_clip(img: Image.Image, start: float, duration: float, position) -> ImageClip:
    clip = ImageClip(np.array(img)).set_start(start).set_duration(duration)
    return clip.set_position(position)


def compose_short(
    title: str,
    captions: list[Caption],
    audio_path: str,
    out_path: str,
    brand_label: str = "한끼정답",
) -> str:
    """
    title: 영상 상단에 고정 표시할 제목
    captions: tts.generate_narration_with_captions()가 반환한 문장 단위 자막 큐
    audio_path: 내레이션 mp3 경로
    out_path: 결과 mp4 저장 경로
    """
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    background = ColorClip((WIDTH, HEIGHT), color=BG_COLOR).set_duration(duration)

    layers = [background]

    title_img = _render_text_image(title, font_size=64, color=TITLE_COLOR, max_width=WIDTH - 160)
    layers.append(_image_clip(title_img, start=0, duration=duration, position=("center", 220)))

    for cap in captions:
        cap_img = _render_text_image(cap.text, font_size=56, color=CAPTION_COLOR, max_width=WIDTH - 160)
        cap_duration = max(cap.end - cap.start, 0.1)
        layers.append(_image_clip(cap_img, start=cap.start, duration=cap_duration, position=("center", "center")))

    brand_img = _render_text_image(brand_label, font_size=36, color=ACCENT_COLOR, max_width=WIDTH - 160, shadow=False)
    layers.append(_image_clip(brand_img, start=0, duration=duration, position=("center", HEIGHT - 140)))

    video = CompositeVideoClip(layers, size=(WIDTH, HEIGHT)).set_audio(audio).set_duration(duration)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    video.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac", logger=None)

    return out_path


if __name__ == "__main__":
    from tts import generate_narration_with_captions_sync, VOICE_FEMALE

    sample_title = "단백질, 하루 몇 그램이 적당할까?"
    sample_script = (
        "오늘의 건강 상식입니다. 단백질은 근육뿐 아니라 면역력 유지에도 중요한 역할을 합니다. "
        "일반적으로 체중 1킬로그램당 하루 1점 2그램에서 1점 6그램 정도가 권장된다고 알려져 있습니다. "
        "이 정보는 일반적인 영양 정보이며, 의학적 진단이나 치료를 대체하지 않습니다."
    )

    audio_path, caps = generate_narration_with_captions_sync(
        sample_script, "video-pipeline/samples/sample_narration.mp3", voice=VOICE_FEMALE
    )
    out = compose_short(sample_title, caps, audio_path, "video-pipeline/samples/sample_short.mp4")
    print(f"영상 생성 완료: {out}")
