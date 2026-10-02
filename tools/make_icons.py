"""Generate PWA icons and favicon for Fracciones Continuas."""
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "icons")
os.makedirs(OUT, exist_ok=True)

INDIGO_TOP = (99, 102, 241)   # indigo-500
INDIGO_BOT = (79, 70, 229)    # indigo-600
VIOLET = (124, 58, 237)       # violet-600
WHITE = (255, 255, 255)


def gradient(size, top, bottom):
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        # diagonal-ish blend toward violet on the right via x sampling in draw step
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (size, y)], fill=c)
    return img


def font(sz):
    for name in ("arialbd.ttf", "arial.ttf", "seguisb.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", sz)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_glyph(img, s):
    """Stylized continued fraction: 1 over bar over nested 1+1/..."""
    d = ImageDraw.Draw(img)
    f_big = font(int(s * 0.34))
    f_small = font(int(s * 0.22))
    f_tiny = font(int(s * 0.16))

    def center_text(y, text, f):
        bbox = d.textbbox((0, 0), text, font=f)
        d.text(((s - (bbox[2] - bbox[0])) / 2 - bbox[0], y), text, font=f, fill=WHITE)
        return bbox[3] - bbox[1]

    # numerator "1"
    cy = s * 0.10
    center_text(cy, "1", f_big)

    # main fraction bar
    bar_y = s * 0.50
    d.rounded_rectangle([s * 0.14, bar_y - s * 0.035, s * 0.86, bar_y + s * 0.035],
                        radius=s * 0.02, fill=WHITE)

    # denominator: "1 + 1/n"
    cy = s * 0.58
    bbox = d.textbbox((0, 0), "1 +", font=f_small)
    w = bbox[2] - bbox[0]
    x0 = s * 0.50 - w / 2 - s * 0.08
    d.text((x0, cy), "1 +", font=f_small, fill=WHITE)
    # nested bar
    nb_y = cy + (bbox[3] - bbox[1]) * 1.15 + s * 0.04
    d.rounded_rectangle([x0, nb_y, x0 + w, nb_y + s * 0.02], radius=s * 0.01, fill=WHITE)
    d.text((x0 + w * 0.1, nb_y + s * 0.035), "n", font=f_tiny, fill=WHITE)


def make_icon(size, maskable=False, rounded=True):
    img = gradient(size, INDIGO_TOP, VIOLET)
    d = ImageDraw.Draw(img)
    if maskable:
        draw_glyph(img, size)  # glyph is within central ~72% safe zone already
        return img
    if rounded:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                               radius=int(size * 0.22), fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(img, (0, 0), mask)
        draw_glyph(out, size)
        return out
    draw_glyph(img, size)
    return img


# Regular "any" icons (rounded corners, transparent outside)
for s in (192, 512, 144, 96, 72, 48, 32, 16):
    make_icon(s).save(os.path.join(OUT, f"icon-{s}.png"))

# Maskable icons (full-bleed)
for s in (192, 512):
    make_icon(s, maskable=True).save(os.path.join(OUT, f"maskable-{s}.png"))

# Apple touch icon (180, full-bleed square, iOS applies its own rounding)
make_icon(180, rounded=False).save(os.path.join(OUT, "apple-touch-icon.png"))

# favicon.ico (16 + 32 + 48)
imgs = [Image.open(os.path.join(OUT, f"icon-{s}.png")) for s in (16, 32, 48)]
imgs[0].save(os.path.join(os.path.dirname(__file__), "..", "favicon.ico"),
             format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=imgs[1:])

print("icons written to", os.path.abspath(OUT))
