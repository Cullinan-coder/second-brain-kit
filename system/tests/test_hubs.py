from sb import hubs


def _w(v, rel, text="x"):
    p = v / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_dizin_notlari(tmp_path):
    v = tmp_path
    _w(v, "60-Kişiler/Ali.md")
    _w(v, "60-Kişiler/Veli.md", "bkz [[Ali]]")
    _w(v, "40-Kaynaklar/Keep/Not.md")
    _w(v, "90-Arşiv/60-Kişiler/Eski.md")
    _w(v, "Dashboard.md", "# D")
    _w(v, "ayar/fetch.yaml", "a: 1")
    assert hubs.orphans(v) == ["40-Kaynaklar/Keep/Not.md", "90-Arşiv/60-Kişiler/Eski.md", "Dashboard.md"]
    hubs.build(v)
    assert "Not" in (v / "40-Kaynaklar/Dizinler/Dizin – Keep.md").read_text(encoding="utf-8")
    assert not (v / "40-Kaynaklar/Dizinler/Dizin – Kişiler.md").exists()
    assert "[[40-Kaynaklar/Dizinler/Dizinler" in (v / "Dashboard.md").read_text(encoding="utf-8")
    _w(v, "40-Kaynaklar/Keep/Not.md", "[[Ali]]")
    hubs.build(v)                                                            # artık bağlı: grup dizini kalkar, tekrar çalışma kararlı
    assert not (v / "40-Kaynaklar/Dizinler/Dizin – Keep.md").exists()
    hubs.build(v)


def test_md_olmayan_dosyalar_baglanir(tmp_path):
    _w(tmp_path, "ayar/fetch.yaml", "a: 1")
    _w(tmp_path, "_system/sb/gizli.py", "x")
    hubs.build(tmp_path)
    t = (tmp_path / "40-Kaynaklar/Dizinler/Dosyalar – ayar.md").read_text(encoding="utf-8")
    assert "[[ayar/fetch.yaml]]" in t
    assert not list((tmp_path / "40-Kaynaklar/Dizinler").glob("*_system sb*"))
