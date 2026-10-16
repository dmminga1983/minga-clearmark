import io

from PIL import Image

from clearmark.imageclean import clean_image, clean_image_bytes, inspect_image


def _make_png_with_text_chunk(path, keyword="Software", value="Midjourney v6"):
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    from PIL.PngImagePlugin import PngInfo

    meta = PngInfo()
    meta.add_text(keyword, value)
    img.save(path, pnginfo=meta)


def test_inspect_finds_png_text_chunk(tmp_path):
    p = tmp_path / "shot.png"
    _make_png_with_text_chunk(p)
    report = inspect_image(p)
    assert report.suspicious
    assert any(f.kind == "text_chunk" for f in report.findings)


def test_clean_image_strips_text_chunk(tmp_path):
    src = tmp_path / "shot.png"
    dst = tmp_path / "shot.cleaned.png"
    _make_png_with_text_chunk(src)
    removed = clean_image(src, dst)
    assert removed >= 1
    report_after = inspect_image(dst)
    assert not report_after.suspicious


def test_clean_plain_image_reports_zero(tmp_path):
    src = tmp_path / "plain.png"
    Image.new("RGB", (4, 4), color=(1, 2, 3)).save(src)
    dst = tmp_path / "plain.cleaned.png"
    removed = clean_image(src, dst)
    assert removed == 0
    # Pixel data must survive untouched.
    with Image.open(dst) as out:
        assert out.getpixel((0, 0)) == (1, 2, 3)


def test_clean_image_bytes_roundtrip():
    buf = io.BytesIO()
    Image.new("RGB", (2, 2), color=(5, 5, 5)).save(buf, format="PNG")
    cleaned, removed = clean_image_bytes(buf.getvalue())
    assert removed == 0
    with Image.open(io.BytesIO(cleaned)) as out:
        assert out.size == (2, 2)
