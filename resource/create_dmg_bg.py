#!/usr/bin/env python3
"""DMG 배경 이미지 생성 스크립트 (660×400, Pillow 사용)"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_dmg_background(output: Path | str = None) -> Path:
    if output is None:
        output = Path(__file__).parent / "dmg-background.png"
    output = Path(output)

    W, H = 660, 400
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # 밝은 그라데이션 배경 (위→아래, 흰색→연한 회색)
    for y in range(H):
        r = int(245 - (y / H) * 25)
        g = int(247 - (y / H) * 25)
        b = int(250 - (y / H) * 20)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 화살표 (앱 아이콘 → Applications 방향, 중앙)
    arrow_y = 190
    arrow_x_start = 260
    arrow_x_end = 400
    shaft_half = 8
    head_half = 22
    head_len = 30

    # 화살표 색상 (부드러운 파란색)
    arrow_color = (90, 140, 210)

    # 몸통
    draw.rectangle(
        [arrow_x_start, arrow_y - shaft_half, arrow_x_end - head_len, arrow_y + shaft_half],
        fill=arrow_color,
    )
    # 머리 (삼각형)
    draw.polygon(
        [
            (arrow_x_end - head_len, arrow_y - head_half),
            (arrow_x_end, arrow_y),
            (arrow_x_end - head_len, arrow_y + head_half),
        ],
        fill=arrow_color,
    )

    # 텍스트
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = font_large

    text_color = (100, 100, 100)

    # 앱 이름 레이블 (왼쪽 아이콘 아래)
    draw.text((155, 250), "YT-Chita", fill=text_color, font=font_large, anchor="mt")

    # Applications 레이블 (오른쪽 아이콘 아래)
    draw.text((480, 250), "Applications", fill=text_color, font=font_large, anchor="mt")

    # 하단 안내
    draw.text(
        (W // 2, H - 40),
        "Drag YT-Chita to Applications to install",
        fill=(130, 130, 130),
        font=font_small,
        anchor="mt",
    )

    img.save(output, "PNG")
    print(f"✅ DMG 배경 이미지 생성: {output}")
    return output


if __name__ == "__main__":
    create_dmg_background()
