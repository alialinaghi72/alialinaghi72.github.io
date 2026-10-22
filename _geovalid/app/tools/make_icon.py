"""Draw the application icon (icon.png 256 px + multi-size icon.ico) with Pillow."""
from pathlib import Path

from PIL import Image, ImageDraw


def draw(size=256):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size / 256
    d.rounded_rectangle([8 * s, 8 * s, 248 * s, 248 * s], radius=44 * s, fill=(31, 42, 48, 255))
    d.rectangle([28 * s, 70 * s, 228 * s, 78 * s], fill=(138, 90, 43, 255))                 # topography
    for k, (x0, col) in enumerate(((70, (94, 156, 139)), (128, (226, 169, 107)), (186, (94, 156, 139)))):
        d.line([(x0 * s, 74 * s), ((x0 + 34) * s, 214 * s)], fill=col + (255,), width=int(12 * s))  # inclined holes
        d.ellipse([(x0 - 9) * s, (74 - 9) * s, (x0 + 9) * s, (74 + 9) * s], fill=(233, 229, 223, 255))
    d.line([(150 * s, 150 * s), (172 * s, 172 * s), (214 * s, 122 * s)], fill=(233, 229, 223, 255), width=int(14 * s))  # check mark
    return im


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "geovalid_pro" / "resources"
    big = draw(256)
    big.save(out / "icon.png")
    big.save(out / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icon written")
