from clearmark.cli import main

ZWSP = chr(0x200B)


def test_cli_inspect_clean_file_exit_zero(tmp_path, capsys):
    f = tmp_path / "plain.txt"
    f.write_text("hello world")
    code = main(["inspect", "--lang", "en", str(f)])
    assert code == 0
    assert "No provenance marks" in capsys.readouterr().out


def test_cli_inspect_finds_marker_exit_two(tmp_path, capsys):
    f = tmp_path / "marked.txt"
    f.write_text("hello" + ZWSP + "world")
    code = main(["inspect", "--lang", "en", str(f)])
    assert code == 2
    assert "Found" in capsys.readouterr().out


def test_cli_clean_writes_output(tmp_path, capsys):
    f = tmp_path / "marked.txt"
    f.write_text("hello" + ZWSP + "world")
    out = tmp_path / "out.txt"
    code = main(["clean", "--lang", "en", str(f), "-o", str(out)])
    assert code == 0
    assert out.read_text() == "helloworld"
    assert "Cleaned" in capsys.readouterr().out


def test_cli_clean_russian_messages(tmp_path, capsys):
    f = tmp_path / "marked.txt"
    f.write_text("hello" + ZWSP + "world")
    out = tmp_path / "out.txt"
    main(["clean", "--lang", "ru", str(f), "-o", str(out)])
    assert "Очищено" in capsys.readouterr().out


def test_cli_missing_file(tmp_path, capsys):
    code = main(["inspect", "--lang", "en", str(tmp_path / "nope.txt")])
    assert code == 1
    assert "not found" in capsys.readouterr().err.lower()
