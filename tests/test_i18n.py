from clearmark.i18n import available_languages, t


def test_en_translation():
    assert t("cli.inspect.clean", "en") == "No provenance marks found."


def test_ru_translation():
    assert t("cli.inspect.clean", "ru") == "Следов ИИ-меток не найдено."


def test_unknown_lang_falls_back_to_english():
    assert t("cli.inspect.clean", "xx") == "No provenance marks found."


def test_available_languages_includes_en_and_ru():
    langs = available_languages()
    assert "en" in langs
    assert "ru" in langs


def test_formatting_with_kwargs():
    assert t("cli.inspect.found", "en", count=3) == "Found 3 potential marker(s):"
    assert t("cli.inspect.found", "ru", count=3) == "Найдено меток: 3"
