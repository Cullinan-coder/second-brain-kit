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
    assert hubs.orphans(v) == ["40-Kaynaklar/Keep/Not.md", "Dashboard.md"]
    hubs.build(v)
    assert "Not" in (v / "40-Kaynaklar/Dizinler/Dizin – Keep.md").read_text(encoding="utf-8")
    assert not (v / "40-Kaynaklar/Dizinler/Dizin – Kişiler.md").exists()
    assert "[[40-Kaynaklar/Dizinler/Dizinler" in (v / "Dashboard.md").read_text(encoding="utf-8")
    _w(v, "40-Kaynaklar/Keep/Not.md", "[[Ali]]")
    hubs.build(v)                                                            # artık bağlı: grup dizini kalkar, tekrar çalışma kararlı
    assert not (v / "40-Kaynaklar/Dizinler/Dizin – Keep.md").exists()
    hubs.build(v)
