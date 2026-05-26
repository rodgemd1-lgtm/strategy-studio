#!/usr/bin/env python3
"""Create the local RIG GTM CRM macOS app icon.

The generated icon is intentionally local and deterministic: no network calls,
no design-service dependency, and the resulting PNG/ICNS can be regenerated.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "apps/desktop-launchers/assets"
SOURCE_APP = ROOT / "apps/desktop-launchers/RIG GTM CRM.app"
DESKTOP_APP = Path("/Users/mikerodgers/Desktop/RIG GTM CRM.app")


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def make_icon(size: int = 1024) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    mask = rounded_mask(size, int(size * 0.22))
    bg = Image.new("RGBA", (size, size), "#0F172A")
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(15 + 7 * (1 - t))
        g = int(23 + 48 * t)
        b = int(42 + 52 * t)
        bg_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    img.alpha_composite(Image.composite(bg, Image.new("RGBA", (size, size), (0, 0, 0, 0)), mask))

    inset = int(size * 0.09)
    draw.rounded_rectangle(
        (inset, inset, size - inset, size - inset),
        radius=int(size * 0.16),
        outline=(148, 163, 184, 90),
        width=max(3, size // 80),
    )

    # Pipeline/lattice mark: strategy -> GTM -> proof, with an upward deviation.
    pts = [
        (int(size * 0.22), int(size * 0.67)),
        (int(size * 0.40), int(size * 0.51)),
        (int(size * 0.58), int(size * 0.58)),
        (int(size * 0.76), int(size * 0.35)),
    ]
    shadow = [(x + size // 160, y + size // 160) for x, y in pts]
    draw.line(shadow, fill=(0, 0, 0, 90), width=max(10, size // 32), joint="curve")
    draw.line(pts, fill="#22D3EE", width=max(8, size // 38), joint="curve")
    draw.line([pts[1], (int(size * 0.42), int(size * 0.30)), pts[3]], fill="#38BDF8", width=max(4, size // 85))
    draw.line([pts[0], (int(size * 0.52), int(size * 0.77)), pts[2]], fill="#14B8A6", width=max(4, size // 85))

    for i, (x, y) in enumerate(pts):
        radius = int(size * (0.042 if i in (0, 3) else 0.034))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#F8FAFC")
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="#0F766E", width=max(3, size // 120))

    rig_font = font(int(size * 0.18), bold=True)
    gtm_font = font(int(size * 0.066), bold=True)
    draw.text((int(size * 0.18), int(size * 0.17)), "RIG", font=rig_font, fill="#F8FAFC")
    draw.text((int(size * 0.19), int(size * 0.82)), "GTM CRM", font=gtm_font, fill="#CBD5E1")

    # Small proof hash bar.
    bar = (int(size * 0.59), int(size * 0.82), int(size * 0.80), int(size * 0.87))
    draw.rounded_rectangle(bar, radius=int(size * 0.018), fill="#0F766E")
    draw.text((int(size * 0.61), int(size * 0.815)), "PROOF", font=font(int(size * 0.04), bold=True), fill="#ECFEFF")
    return img


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    png_path = ASSET_DIR / "rig-gtm-crm-icon.png"
    icns_path = ASSET_DIR / "AppIcon.icns"
    iconset = ASSET_DIR / "AppIcon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()

    base = make_icon()
    base.save(png_path)

    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for px in sizes:
        resized = base.resize((px, px), Image.Resampling.LANCZOS)
        if px <= 512:
            resized.save(iconset / f"icon_{px // 2}x{px // 2}@2x.png")
        resized.save(iconset / f"icon_{px}x{px}.png")

    subprocess.run(["/usr/bin/iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)], check=True)

    for app in (SOURCE_APP, DESKTOP_APP):
        resources = app / "Contents/Resources"
        if (app / "Contents").exists():
            resources.mkdir(parents=True, exist_ok=True)
            shutil.copy2(icns_path, resources / "AppIcon.icns")
            subprocess.run(["/usr/bin/touch", str(app)], check=False)

    print(f"PNG: {png_path}")
    print(f"ICNS: {icns_path}")


if __name__ == "__main__":
    main()
