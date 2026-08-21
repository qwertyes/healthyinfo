"""
건강 팁 숏폼(60초, 9:16) 영상 합성 모듈 — v2 (퀄리티 개선판).
v1(단색 배경 + 정적 자막)을 실제로 본 사용자 피드백("업로드하기엔 퀄리티가 낮다") 반영:
  1. 배경 — 정적 단색 대신, 미리 계산한 그라데이션 위에 은은하게 숨쉬는 글로우를 얹은
     애니메이션 배경 (외부 이미지/영상 소재 없이 numpy로 생성, 매 프레임 재계산 없이
     빠르게 렌더링됨)
  2. 자막 — 페이드인/아웃 + 슬라이드업 애니메이션, 가독성을 위한 반투명 라운드 패널
  3. 사운드 — 자막 등장마다 짧은 "pop" 효과음 + 아주 낮은 볼륨의 앰비언트 패드(둘 다
     외부 음원 없이 numpy로 직접 합성 — 라이선스 문제 없음)
  4. 브랜딩 — 제목에 포인트 컬러 언더라인, 워드마크 배지화

ImageMagick 의존성을 피하려고 MoviePy TextClip 대신 PIL로 텍스트를 직접 렌더링한다
(my-video-creator의 english_words_short.py와 같은 접근).
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, VideoClip, vfx
from moviepy.audio.AudioClip import AudioArrayClip

from tts import Caption

WIDTH, HEIGHT = 1080, 1920
FPS = 30
AUDIO_FPS = 44100

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NanumGothic.ttf")

GRADIENT_TOP = np.array([26, 22, 34], dtype=np.float64)  # 짙은 자주빛 남색
GRADIENT_BOTTOM = np.array([14, 16, 24], dtype=np.float64)  # 거의 검정에 가까운 남색
GLOW_COLOR = np.array([255, 160, 80], dtype=np.float64)  # 브랜드 포인트(오렌지)
GLOW_CYCLE_SECONDS = 6.0
GLOW_AMPLITUDE = 22.0  # 0~255 스케일에서 글로우가 더하는 최대 밝기

TITLE_COLOR = (255, 255, 255)
CAPTION_COLOR = (255, 255, 255)
ACCENT_COLOR = (255, 160, 80)
CAPTION_SHADOW = (0, 0, 0)
PANEL_COLOR = (0, 0, 0, 110)  # 자막 뒤 반투명 패널


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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


# ── 배경: 정적 그라데이션 + 저비용 글로우 브리딩 ──────────────────────────────


def _build_gradient_base() -> np.ndarray:
    """세로 그라데이션을 한 번만 계산해 재사용한다 (프레임마다 다시 계산 안 함)."""
    t = np.linspace(0.0, 1.0, HEIGHT).reshape(HEIGHT, 1, 1)
    gradient = GRADIENT_TOP.reshape(1, 1, 3) * (1 - t) + GRADIENT_BOTTOM.reshape(1, 1, 3) * t
    return np.broadcast_to(gradient, (HEIGHT, WIDTH, 3)).copy()


def _build_glow_mask() -> np.ndarray:
    """화면 중상단에 은은한 원형 글로우 마스크를 한 번만 계산한다 (0~1 범위)."""
    cy, cx = HEIGHT * 0.35, WIDTH * 0.5
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    radius = WIDTH * 0.9
    mask = np.clip(1.0 - dist / radius, 0.0, 1.0) ** 2
    return mask


def make_background_clip(duration: float) -> VideoClip:
    base = _build_gradient_base()
    glow_mask = _build_glow_mask()[:, :, None]  # (H, W, 1)

    def make_frame(t: float) -> np.ndarray:
        pulse = 0.5 + 0.5 * np.sin(2 * np.pi * t / GLOW_CYCLE_SECONDS)
        frame = base + glow_mask * GLOW_COLOR.reshape(1, 1, 3) * (GLOW_AMPLITUDE * pulse / 255.0)
        return np.clip(frame, 0, 255).astype("uint8")

    return VideoClip(make_frame, duration=duration)


# ── 자막/제목: PIL 렌더링 + 패널 ──────────────────────────────────────────


def _render_text_panel(
    text: str,
    font_size: int,
    color: tuple[int, int, int],
    max_width: int,
    with_panel: bool = False,
    shadow: bool = True,
) -> Image.Image:
    font = _font(font_size)
    lines = _wrap_text(text, font, max_width)

    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    line_height = int(font_size * 1.5)
    line_widths = [probe.textlength(line, font=font) for line in lines]
    text_width = max(int(max(line_widths, default=0)), 10)
    text_height = line_height * len(lines)

    pad_x, pad_y = (36, 24) if with_panel else (10, 10)
    img_width = text_width + pad_x * 2
    img_height = text_height + pad_y * 2

    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if with_panel:
        draw.rounded_rectangle([0, 0, img_width, img_height], radius=24, fill=PANEL_COLOR)

    for i, line in enumerate(lines):
        line_w = line_widths[i]
        x = (img_width - line_w) / 2
        y = pad_y + i * line_height
        if shadow:
            draw.text((x + 3, y + 3), line, font=font, fill=(*CAPTION_SHADOW, 180))
        draw.text((x, y), line, font=font, fill=(*color, 255))

    return img


def _animated_clip(img: Image.Image, start: float, duration: float, target_y, slide_px: int = 26) -> ImageClip:
    """페이드인/아웃 + 아래→제자리 슬라이드업 애니메이션이 붙은 ImageClip."""
    fade_in = min(0.28, duration / 3)
    fade_out = min(0.22, duration / 4)

    clip = ImageClip(np.array(img)).set_start(start).set_duration(duration)
    clip = clip.fx(vfx.fadein, fade_in).fx(vfx.fadeout, fade_out)

    def pos(t: float):
        progress = min(1.0, t / fade_in) if fade_in > 0 else 1.0
        eased = 1 - (1 - progress) ** 3  # ease-out cubic
        y = target_y + (1 - eased) * slide_px
        return ("center", y)

    return clip.set_position(pos)


# ── 사운드: 절차적 합성(외부 음원 없음) ──────────────────────────────────


def _synthesize_pop(duration: float = 0.12, freq: float = 720.0, volume: float = 0.18) -> np.ndarray:
    n = int(AUDIO_FPS * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    envelope = np.exp(-t * 28)  # 빠른 감쇠
    wave = np.sin(2 * np.pi * freq * t) * envelope * volume
    return np.column_stack([wave, wave])  # 스테레오


def _synthesize_ambient_pad(duration: float, volume: float = 0.035) -> np.ndarray:
    """아주 낮은 볼륨의 은은한 패드(도-솔 화음). BGM 대용 — 나레이션을 방해하지 않는 선."""
    n = int(AUDIO_FPS * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    root, fifth = 130.81, 196.00  # C3, G3
    wave = (np.sin(2 * np.pi * root * t) + 0.6 * np.sin(2 * np.pi * fifth * t)) * volume
    fade_len = min(n // 2, int(AUDIO_FPS * 1.5))
    fade = np.ones(n)
    fade[:fade_len] = np.linspace(0, 1, fade_len)
    fade[-fade_len:] = np.linspace(1, 0, fade_len)
    wave = wave * fade
    return np.column_stack([wave, wave])


def _build_sfx_track(captions: list[Caption], duration: float) -> CompositeAudioClip:
    clips = [AudioArrayClip(_synthesize_ambient_pad(duration), fps=AUDIO_FPS)]
    for cap in captions:
        pop = AudioArrayClip(_synthesize_pop(), fps=AUDIO_FPS).set_start(cap.start)
        clips.append(pop)
    return CompositeAudioClip(clips)


# ── 조립 ──────────────────────────────────────────────────────────────


def compose_short(
    title: str,
    captions: list[Caption],
    audio_path: str,
    out_path: str,
    brand_label: str = "한끼정답",
) -> str:
    narration = AudioFileClip(audio_path)
    duration = narration.duration

    background = make_background_clip(duration)
    layers = [background]

    title_img = _render_text_panel(title, font_size=64, color=TITLE_COLOR, max_width=WIDTH - 160)
    title_clip = ImageClip(np.array(title_img)).set_start(0).set_duration(duration).set_position(("center", 200))
    layers.append(title_clip.fx(vfx.fadein, 0.4))

    underline_w = min(int(title_img.width * 0.5), 220)
    underline = Image.new("RGBA", (underline_w, 6), (*ACCENT_COLOR, 255))
    underline_y = 200 + title_img.height + 14
    layers.append(
        ImageClip(np.array(underline)).set_start(0).set_duration(duration).set_position(("center", underline_y)).fx(
            vfx.fadein, 0.4
        )
    )

    for cap in captions:
        cap_img = _render_text_panel(cap.text, font_size=54, color=CAPTION_COLOR, max_width=WIDTH - 180, with_panel=True)
        cap_duration = max(cap.end - cap.start, 0.1)
        target_y = HEIGHT / 2 - cap_img.height / 2
        layers.append(_animated_clip(cap_img, cap.start, cap_duration, target_y))

    brand_img = _render_text_panel(brand_label, font_size=32, color=ACCENT_COLOR, max_width=WIDTH - 160, shadow=False)
    brand_clip = ImageClip(np.array(brand_img)).set_start(0).set_duration(duration).set_position(("center", HEIGHT - 140))
    layers.append(brand_clip.fx(vfx.fadein, 0.4))

    video = CompositeVideoClip(layers, size=(WIDTH, HEIGHT)).set_duration(duration)

    sfx = _build_sfx_track(captions, duration)
    full_audio = CompositeAudioClip([narration, sfx]).set_duration(duration)
    video = video.set_audio(full_audio)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    video.write_videofile(out_path, fps=FPS, codec="libx264", audio_codec="aac", audio_fps=AUDIO_FPS, logger=None)

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
    out = compose_short(sample_title, caps, audio_path, "video-pipeline/samples/sample_short_v2.mp4")
    print(f"영상 생성 완료: {out}")
