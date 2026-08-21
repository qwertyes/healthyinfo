"""
건강 팁 숏폼(60초, 9:16) 영상 합성 모듈 — v3.
사용자가 v2("배경 사진 1장 + 정적 자막")도 "단조롭다"고 피드백해서, 인기 쇼츠 생성기들이
공통으로 쓰는 3가지 기법을 적용했다:
  1. 배경 — 스톡 사진 1장이 아니라 여러 장을 구간별로 전환 (각 구간마다 켄 번즈 줌인).
     사진을 못 구하면 numpy로 생성한 그라데이션+숨쉬는 글로우 배경으로 자동 폴백.
  2. 자막 — 문장 단위 정적 표시 대신, **단어 단위 카라오케 하이라이트**
     (Typecast TTS의 단어 타임스탬프 기반, typecast_tts.WordTiming 사용)
  3. 폰트 — 나눔고딕(얇음) 대신 굵고 임팩트 있는 Black Han Sans로 교체 (제목/자막용).
     브랜드 워드마크만 나눔고딕 유지 (작은 글자라 얇아도 됨).
  4. 사운드 — 자막 등장마다 짧은 "pop" 효과음 + 아주 낮은 볼륨의 앰비언트 패드(둘 다
     외부 음원 없이 numpy로 직접 합성 — 라이선스 문제 없음)

ImageMagick 의존성을 피하려고 MoviePy TextClip 대신 PIL로 텍스트를 직접 렌더링한다
(my-video-creator의 english_words_short.py와 같은 접근). MoviePy 1.0.3의 내장 .resize()는
최신 Pillow(10+)에서 제거된 Image.ANTIALIAS를 참조해 깨지므로, 줌 효과도 직접 프레임을
만들어서 우회한다.
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, VideoClip, vfx
from moviepy.audio.AudioClip import AudioArrayClip

from typecast_tts import WordTiming

WIDTH, HEIGHT = 1080, 1920
FPS = 30
AUDIO_FPS = 44100

FONT_BOLD_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "BlackHanSans-Regular.ttf")
FONT_REGULAR_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NanumGothic.ttf")

GRADIENT_TOP = np.array([26, 22, 34], dtype=np.float64)  # 짙은 자주빛 남색
GRADIENT_BOTTOM = np.array([14, 16, 24], dtype=np.float64)  # 거의 검정에 가까운 남색
GLOW_COLOR = np.array([255, 160, 80], dtype=np.float64)  # 브랜드 포인트(오렌지)
GLOW_CYCLE_SECONDS = 6.0
GLOW_AMPLITUDE = 22.0  # 0~255 스케일에서 글로우가 더하는 최대 밝기

TITLE_COLOR = (255, 255, 255)
CAPTION_COLOR = (255, 255, 255)
ACCENT_COLOR = (255, 160, 80)
CAPTION_SHADOW = (0, 0, 0)
PANEL_COLOR = (0, 0, 0, 130)  # 자막 뒤 반투명 패널

KARAOKE_MAX_CHARS = 16  # 자막 한 줄당 최대 글자 수 (대략)


def _font_bold(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD_PATH, size)


def _font_regular(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_REGULAR_PATH, size)


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


# ── 배경: 그라데이션 + 저비용 글로우 브리딩 (사진 못 구했을 때 폴백) ──────────────


def _build_gradient_base() -> np.ndarray:
    t = np.linspace(0.0, 1.0, HEIGHT).reshape(HEIGHT, 1, 1)
    gradient = GRADIENT_TOP.reshape(1, 1, 3) * (1 - t) + GRADIENT_BOTTOM.reshape(1, 1, 3) * t
    return np.broadcast_to(gradient, (HEIGHT, WIDTH, 3)).copy()


def _build_glow_mask() -> np.ndarray:
    cy, cx = HEIGHT * 0.35, WIDTH * 0.5
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    radius = WIDTH * 0.9
    mask = np.clip(1.0 - dist / radius, 0.0, 1.0) ** 2
    return mask


def make_gradient_background_clip(duration: float) -> VideoClip:
    base = _build_gradient_base()
    glow_mask = _build_glow_mask()[:, :, None]

    def make_frame(t: float) -> np.ndarray:
        pulse = 0.5 + 0.5 * np.sin(2 * np.pi * t / GLOW_CYCLE_SECONDS)
        frame = base + glow_mask * GLOW_COLOR.reshape(1, 1, 3) * (GLOW_AMPLITUDE * pulse / 255.0)
        return np.clip(frame, 0, 255).astype("uint8")

    return VideoClip(make_frame, duration=duration)


# ── 배경: 스톡 사진 여러 장 구간 전환 + 켄 번즈 줌 ────────────────────────────


def _load_cover_image(path: str, target_w: int, target_h: int) -> Image.Image:
    """이미지를 target 비율에 맞춰 꽉 채우도록 리사이즈 + 중앙 크롭한다."""
    img = Image.open(path).convert("RGB")
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_height = target_h
        new_width = int(target_h * src_ratio)
    else:
        new_width = target_w
        new_height = int(target_w / src_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - target_w) // 2
    top = (new_height - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _build_dark_overlay() -> np.ndarray:
    """사진 위에 얹을 반투명 오버레이(RGBA) — 위/아래는 어둡게, 가운데는 옅게 해서 텍스트 가독성 확보."""
    t = np.linspace(0.0, 1.0, HEIGHT)
    darkness = 0.72 * (1 - np.sin(np.pi * t)) + 0.30
    alpha = np.clip(darkness * 255, 0, 255).astype("uint8")
    overlay = np.zeros((HEIGHT, WIDTH, 4), dtype="uint8")
    overlay[:, :, 3] = alpha[:, None]
    return overlay


def _prepare_zoom_source(photo_path: str, zoom_amount: float) -> np.ndarray:
    oversized_w = int(WIDTH * (1 + zoom_amount))
    oversized_h = int(HEIGHT * (1 + zoom_amount))
    return np.array(_load_cover_image(photo_path, oversized_w, oversized_h))


def make_photo_background_clip(photo_paths: list[str], duration: float) -> VideoClip:
    """
    스톡 사진 여러 장을 구간별로 전환하며, 각 구간마다 느린 줌인(켄 번즈)을 준다.
    위에 어둡게 오버레이해서 자막 가독성을 확보한다.
    MoviePy 내장 .resize()가 최신 Pillow에서 깨지는 문제(Image.ANTIALIAS 제거)를 피하려고
    프레임을 직접 numpy/PIL로 생성한다.
    """
    zoom_amount = 0.08
    n = len(photo_paths)
    segment_duration = duration / n
    sources = [_prepare_zoom_source(p, zoom_amount) for p in photo_paths]

    overlay = _build_dark_overlay().astype(np.float64)
    overlay_rgb = overlay[:, :, :3]
    overlay_alpha = overlay[:, :, 3:4] / 255.0

    def make_frame(t: float) -> np.ndarray:
        idx = min(n - 1, int(t // segment_duration))
        local_t = t - idx * segment_duration
        progress = min(1.0, local_t / segment_duration) if segment_duration > 0 else 1.0

        src = sources[idx]
        src_h, src_w = src.shape[:2]
        crop_w = int(src_w - (src_w - WIDTH) * progress)
        crop_h = int(src_h - (src_h - HEIGHT) * progress)
        x0 = (src_w - crop_w) // 2
        y0 = (src_h - crop_h) // 2
        cropped = src[y0 : y0 + crop_h, x0 : x0 + crop_w]
        frame_img = Image.fromarray(cropped).resize((WIDTH, HEIGHT), Image.LANCZOS)
        frame = np.asarray(frame_img, dtype=np.float64)
        blended = frame * (1 - overlay_alpha) + overlay_rgb * overlay_alpha
        return np.clip(blended, 0, 255).astype("uint8")

    return VideoClip(make_frame, duration=duration)


# ── 자막: 단어 단위 카라오케 하이라이트 ───────────────────────────────────


def group_words_into_lines(words: list[WordTiming], max_chars: int = KARAOKE_MAX_CHARS) -> list[list[WordTiming]]:
    """단어를 화면에 한 줄로 보여줄 만큼씩 묶는다."""
    lines: list[list[WordTiming]] = []
    current: list[WordTiming] = []
    current_len = 0
    for w in words:
        w_len = len(w.text) + 1
        if current and current_len + w_len > max_chars:
            lines.append(current)
            current = []
            current_len = 0
        current.append(w)
        current_len += w_len
    if current:
        lines.append(current)
    return lines


def _render_karaoke_frame(word_texts: list[str], highlight_idx: int, font_size: int) -> Image.Image:
    """한 줄의 모든 단어를 그리되, highlight_idx번째 단어만 포인트 컬러로 강조한다.
    같은 줄의 모든 프레임이 동일한 캔버스 크기를 쓰도록 전체 텍스트 기준으로 크기를 잡는다
    (그래야 단어가 바뀔 때 패널 크기가 흔들리지 않는다)."""
    font = _font_bold(font_size)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    full_line = " ".join(word_texts)

    pad_x, pad_y = 32, 20
    line_w = probe.textlength(full_line, font=font)
    img_w = int(line_w) + pad_x * 2
    img_h = int(font_size * 1.4) + pad_y * 2

    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, img_w, img_h], radius=22, fill=PANEL_COLOR)

    x = pad_x
    y = pad_y
    for i, word in enumerate(word_texts):
        color = ACCENT_COLOR if i == highlight_idx else CAPTION_COLOR
        draw.text((x + 3, y + 3), word, font=font, fill=(*CAPTION_SHADOW, 180))
        draw.text((x, y), word, font=font, fill=(*color, 255))
        x += probe.textlength(word + " ", font=font)

    return img


def _karaoke_line_clips(line: list[WordTiming], target_y: float, font_size: int) -> list[ImageClip]:
    """한 줄(여러 단어)을, 단어가 바뀔 때마다 하이라이트만 이동하는 클립들로 만든다."""
    word_texts = [w.text for w in line]
    line_end = line[-1].end
    clips = []

    for i, w in enumerate(line):
        seg_start = w.start
        seg_end = line[i + 1].start if i + 1 < len(line) else line_end
        seg_duration = max(seg_end - seg_start, 0.05)

        img = _render_karaoke_frame(word_texts, i, font_size)
        clip = ImageClip(np.array(img)).set_start(seg_start).set_duration(seg_duration)
        clip = clip.set_position(("center", target_y))
        clips.append(clip)

    if clips:
        clips[0] = clips[0].fx(vfx.fadein, min(0.15, clips[0].duration))
        clips[-1] = clips[-1].fx(vfx.fadeout, min(0.15, clips[-1].duration))

    return clips


# ── 사운드: 절차적 합성(외부 음원 없음) ──────────────────────────────────


def _synthesize_pop(duration: float = 0.10, freq: float = 720.0, volume: float = 0.14) -> np.ndarray:
    n = int(AUDIO_FPS * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    envelope = np.exp(-t * 32)
    wave = np.sin(2 * np.pi * freq * t) * envelope * volume
    return np.column_stack([wave, wave])


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
    return np.column_stack([wave * fade, wave * fade])


def _build_sfx_track(lines: list[list[WordTiming]], duration: float) -> CompositeAudioClip:
    """자막 줄이 새로 시작될 때마다(단어마다는 너무 잦아서) pop 효과음을 준다."""
    clips = [AudioArrayClip(_synthesize_ambient_pad(duration), fps=AUDIO_FPS)]
    for line in lines:
        pop = AudioArrayClip(_synthesize_pop(), fps=AUDIO_FPS).set_start(line[0].start)
        clips.append(pop)
    return CompositeAudioClip(clips)


# ── 조립 ──────────────────────────────────────────────────────────────


def compose_short(
    title: str,
    words: list[WordTiming],
    audio_path: str,
    out_path: str,
    brand_label: str = "한끼정답",
    background_photo_paths: list[str] | None = None,
) -> str:
    narration = AudioFileClip(audio_path)
    duration = narration.duration

    if background_photo_paths:
        background = make_photo_background_clip(background_photo_paths, duration)
    else:
        background = make_gradient_background_clip(duration)
    layers = [background]

    title_img = _render_text_title(title)
    title_clip = ImageClip(np.array(title_img)).set_start(0).set_duration(duration).set_position(("center", 190))
    layers.append(title_clip.fx(vfx.fadein, 0.4))

    underline_w = min(int(title_img.width * 0.5), 220)
    underline = Image.new("RGBA", (underline_w, 6), (*ACCENT_COLOR, 255))
    underline_y = 190 + title_img.height + 14
    layers.append(
        ImageClip(np.array(underline)).set_start(0).set_duration(duration).set_position(("center", underline_y)).fx(
            vfx.fadein, 0.4
        )
    )

    caption_font_size = 52
    caption_line_height = int(caption_font_size * 1.4) + 20 * 2
    target_y = HEIGHT / 2 - caption_line_height / 2

    lines = group_words_into_lines(words)
    for line in lines:
        layers.extend(_karaoke_line_clips(line, target_y, caption_font_size))

    brand_img = _render_text_brand(brand_label)
    brand_clip = ImageClip(np.array(brand_img)).set_start(0).set_duration(duration).set_position(("center", HEIGHT - 140))
    layers.append(brand_clip.fx(vfx.fadein, 0.4))

    video = CompositeVideoClip(layers, size=(WIDTH, HEIGHT)).set_duration(duration)

    sfx = _build_sfx_track(lines, duration)
    full_audio = CompositeAudioClip([narration, sfx]).set_duration(duration)
    video = video.set_audio(full_audio)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    video.write_videofile(out_path, fps=FPS, codec="libx264", audio_codec="aac", audio_fps=AUDIO_FPS, logger=None)

    return out_path


def _render_text_title(text: str) -> Image.Image:
    font = _font_bold(60)
    lines = _wrap_text(text, font, WIDTH - 160)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    line_height = int(60 * 1.35)
    line_widths = [probe.textlength(line, font=font) for line in lines]
    img_w = max(int(max(line_widths, default=0)), 10) + 20
    img_h = line_height * len(lines) + 20
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        x = (img_w - line_widths[i]) / 2
        y = 10 + i * line_height
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 190))
        draw.text((x, y), line, font=font, fill=(*TITLE_COLOR, 255))
    return img


def _render_text_brand(text: str) -> Image.Image:
    font = _font_regular(32)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = int(probe.textlength(text, font=font)) + 20
    h = int(32 * 1.5) + 10
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10, 5), text, font=font, fill=(*ACCENT_COLOR, 255))
    return img


if __name__ == "__main__":
    from stock_photo import search_photos
    from typecast_tts import generate_narration_with_words

    sample_title = "단백질, 하루 몇 그램이 적당할까?"
    sample_script = (
        "오늘의 건강 상식입니다. 단백질은 근육뿐 아니라 면역력 유지에도 중요한 역할을 합니다. "
        "일반적으로 체중 1킬로그램당 하루 1점 2그램에서 1점 6그램 정도가 권장된다고 알려져 있습니다. "
        "이 정보는 일반적인 영양 정보이며, 의학적 진단이나 치료를 대체하지 않습니다."
    )

    audio_path, duration, words = generate_narration_with_words(
        sample_script, "video-pipeline/samples/sample_narration_v3.wav"
    )
    photo_paths = search_photos("grilled chicken breast", "video-pipeline/samples/bg_v3", count=3)
    out = compose_short(
        sample_title, words, audio_path, "video-pipeline/samples/sample_short_v4.mp4",
        background_photo_paths=photo_paths,
    )
    print(f"영상 생성 완료: {out} (배경 사진 {len(photo_paths)}장)")
