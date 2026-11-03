from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.dictpacks.loader import load_glossary
from lexaudit.sources.collect import collect_all, collect_files
from lexaudit.sources.formats import (
    collect_docusaurus,
    collect_html_file,
    collect_i18n_file,
    collect_mkdocs,
    collect_po_file,
    collect_rst_file,
    collect_vitepress,
    collect_xliff_file,
    html_to_text,
    rst_to_text,
)

FIX = Path(__file__).parent / "fixtures" / "formats"


def test_html_strips_script() -> None:
    text = html_to_text("<p>Hi</p><script>bad()</script><p>orientir</p>")
    assert "bad" not in text
    assert "orientir" in text


def test_po_and_xliff_and_html() -> None:
    po = collect_po_file(FIX / "po" / "messages.po", "messages.po")
    assert any("orientir" in c.text for c in po)
    assert any("denseness" in c.text for c in po)
    xl = collect_xliff_file(FIX / "xliff" / "sample.xliff", "sample.xliff")
    assert any("orientir" in c.text for c in xl)
    ht = collect_html_file(FIX / "html" / "page.html", "page.html")
    assert any("orientir" in c.text for c in ht)


def test_mkdocs_docusaurus_vitepress() -> None:
    mk = collect_mkdocs(FIX / "mkdocs", "en")
    assert mk and any("orientir" in c.text for c in mk)
    du = collect_docusaurus(FIX / "docusaurus", "en")
    assert du and any("denseness" in c.text for c in du)
    vp = collect_vitepress(FIX / "vitepress", "en")
    assert vp and any("surveyness" in c.text for c in vp)


def test_collect_files_walks_new_suffixes() -> None:
    chunks = collect_files(FIX / "html", "en", files_paths=(FIX / "html",))
    assert any(c.source == "files" for c in chunks)


def test_collect_all_source_flags() -> None:
    chunks = collect_all(FIX / "mkdocs", "en", sources={"mkdocs"})
    assert chunks


def test_rst_strips_directives_roles_literals(tmp_path: Path) -> None:
    rst = tmp_path / "page.rst"
    rst.write_text(
        "Title\n=====\n\n"
        "See :ref:`label` and ``code_literal`` here.\n\n"
        ".. code-block:: python\n\n"
        "   print('secret')\n\n"
        "The orientir value remains.\n",
        encoding="utf-8",
    )
    plain = rst_to_text(rst.read_text(encoding="utf-8"))
    assert "secret" not in plain
    assert "code_literal" not in plain
    assert "label" in plain
    assert "orientir" in plain
    chunks = collect_rst_file(rst, "page.rst")
    assert chunks and "orientir" in chunks[0].text
    assert "print" not in chunks[0].text


def test_i18n_json_yaml_leaf_key_paths(tmp_path: Path) -> None:
    js = tmp_path / "ru.json"
    js.write_text(
        json_dumps := '{"nav": {"home": "orientir home", "items": ["denseness"]}}',
        encoding="utf-8",
    )
    del json_dumps
    chunks = collect_i18n_file(js, "ru.json")
    scopes = {c.scope: c.text for c in chunks}
    assert scopes["nav.home"] == "orientir home"
    assert scopes["nav.items[0]"] == "denseness"

    yml = tmp_path / "messages.yaml"
    yml.write_text(
        "buttons:\n  save: surveyness save\n  nested:\n    ok: fine\n",
        encoding="utf-8",
    )
    ychunks = collect_i18n_file(yml, "messages.yaml")
    yscopes = {c.scope: c.text for c in ychunks}
    assert yscopes["buttons.save"] == "surveyness save"
    assert yscopes["buttons.nested.ok"] == "fine"


def test_glossary_csv_yaml_and_cli_flag(tmp_path: Path) -> None:
    csv_path = tmp_path / "glossary.csv"
    csv_path.write_text("term,note\norientir,allow\nCustomBrand,\n", encoding="utf-8")
    terms = load_glossary(csv_path, "en")
    assert "orientir" in terms
    assert "custombrand" in terms

    yaml_path = tmp_path / "glossary.yaml"
    yaml_path.write_text("terms:\n  - denseness\n  - FooBar\n", encoding="utf-8")
    yterms = load_glossary(yaml_path, "en")
    assert "denseness" in yterms
    assert "foobar" in yterms

    page = tmp_path / "page.md"
    page.write_text("# Page\n\nThe orientir value.\n", encoding="utf-8")
    runner = CliRunner()
    # Without glossary: calque fails --check
    fail = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(page),
            "--locale",
            "en",
            "--check",
            "--no-fetch-dicts",
            "--no-html",
        ],
    )
    assert fail.exit_code == 1, fail.output
    # With glossary: orientir allowed as proper → check passes
    ok = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(page),
            "--locale",
            "en",
            "--check",
            "--no-fetch-dicts",
            "--no-html",
            "--glossary",
            str(csv_path),
        ],
    )
    assert ok.exit_code == 0, ok.output
