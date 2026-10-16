from clearmark.textclean import clean_text, inspect_text

ZWSP = chr(0x200B)
LRE = chr(0x202A)
PDF = chr(0x202C)
NBSP = chr(0x00A0)
SOFT_HYPHEN = chr(0x00AD)
TAG_LATIN_SMALL_A = chr(0xE0061)
CANCEL_TAG = chr(0xE0001)


def test_detects_zero_width_space():
    text = "Hello" + ZWSP + "World"
    report = inspect_text(text)
    assert report.suspicious
    assert report.total == 1
    assert report.findings[0].category == "zero_width"


def test_clean_removes_zero_width_and_bidi():
    text = "a" + ZWSP + "b" + LRE + "c" + PDF
    cleaned, removed = clean_text(text)
    assert cleaned == "abc"
    assert removed == 3


def test_clean_normalizes_exotic_space_by_default():
    text = "a" + NBSP + "b"
    cleaned, removed = clean_text(text)
    assert cleaned == "a b"
    assert removed == 1


def test_clean_can_preserve_exotic_spaces():
    text = "a" + NBSP + "b"
    cleaned, removed = clean_text(text, normalize_spaces=False)
    assert cleaned == text
    assert removed == 0


def test_plain_text_is_clean():
    text = "Just a normal sentence, with punctuation! And numbers 123."
    report = inspect_text(text)
    assert not report.suspicious
    cleaned, removed = clean_text(text)
    assert cleaned == text
    assert removed == 0


def test_russian_text_untouched():
    text = "Обычный текст на русском языке без меток."
    report = inspect_text(text)
    assert not report.suspicious
    cleaned, removed = clean_text(text)
    assert cleaned == text
    assert removed == 0


def test_soft_hyphen_and_tag_chars_removed():
    text = "co" + SOFT_HYPHEN + "operate" + TAG_LATIN_SMALL_A + CANCEL_TAG
    cleaned, removed = clean_text(text)
    assert cleaned == "cooperate"
    assert removed == 3
