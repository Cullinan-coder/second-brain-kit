"""UZEM/Moodle ayrıştırıcı: anonim (uydurma) Moodle 4.x ders sayfası fikstürüyle bölüm/etkinlik/tür, eşleme, tarih ve metin yardımcıları."""
from datetime import datetime

import pytest

from sb import uzem_sync as us

BASE = "https://lms.universite.edu.tr"


def act_html(tur: str, mid: int, ad: str, extra: str = "", accessible: str = "") -> str:
    return f'''<li class="activity {tur} modtype_{tur} hasinfo "
    id="module-{mid}" data-for="cmitem" data-id="{mid}" >
  <div class="activity-item focus-control " data-activityname="{ad.replace("&", "&amp;amp;")}" data-region="activity-card">
    <div class="activity-name-area"><div class="activitytitle modtype_{tur}"><div class="activityname">
      <a href="{BASE}/mod/{tur}/view.php?id={mid}" class=" aalink stretched-link"><span class="instancename">{ad.replace("&", "&amp;")} <span class="accesshide "> {accessible}</span></span></a>
    </div></div></div>{extra}
  </div></li>'''


def course_html(cid: int, title: str, sections: list) -> str:
    out = [f'<html><head><title>Ders: {title} | FAKÜLTE 26-27 GÜZ</title></head><body id="page-course-view-weeks" class="format-weeks course-{cid} path-course">']
    for n, (name, acts) in enumerate(sections):
        out.append(f'<li id="section-{n}" class="section course-section main clearfix " data-sectionid="{n}" data-sectionreturnnum="" '
                   f'data-for="section" data-id="{900 + n}" data-number="{n}" data-sectionname="{name}" ><div class="section-item">'
                   f'<h3 class="sectionname"><a href="{BASE}/course/section.php?id={900 + n}">{name}</a></h3><ul class="section m-0 p-0" data-for="cmlist">')
        out.extend(acts)
        out.append("</ul></div></li>")
    out.append("</body></html>")
    return "\n".join(out)


DUE = ('<div data-region="activity-dates" class="activity-dates me-sm-2"><div class="date-item"><span class="date-item-label">Açıldığı tarih:</span> '
       'Salı, 29 Eylül 2026, 12:00 AM </div><div class="date-item"><span class="date-item-label">Son yükleme tarihi:</span> '
       'Salı, 6 Ekim 2026, 12:00 AM </div></div>')
LABEL_BODY = ('<div class="activity-altcontent text-break "><div class="no-overflow"><p>Değerli öğrenciler,</p>'
              '<ul><li>Ödev <b>değerlendirildi</b></li></ul><!-- sb:auto:x:start --></div></div>')
PAGE_BODY = '<div class="activity-altcontent text-break activity-description"><div class="no-overflow"><p><b>Bölüm 1: Giriş</b></p></div></div>'


@pytest.fixture()
def html():
    sec = [("Genel", [act_html("forum", 101, "Duyurular", accessible="Forum")]),
           ("21 Eylül - 27 Eylül", [act_html("resource", 111, "1. Giriş & Temeller", accessible="Dosya"),
                                    act_html("resource", 111, "1. Giriş & Temeller", accessible="Dosya"),     # sayfada ikinci kez geçen
                                    act_html("folder", 112, "Dosyalar", accessible="Klasör"),
                                    act_html("assign", 113, "Ödev 1", DUE, "Ödev")]),
           ("28 Eylül - 4 Ekim", [act_html("label", 114, "Not", LABEL_BODY), act_html("page", 115, "Konu Başlıkları", PAGE_BODY, "Sayfa"),
                                  act_html("url", 116, "Kaynak sitesi", accessible="URL"), act_html("choice", 117, "Sunum günü", accessible="Anket"),
                                  act_html("lesson", 118, "Online ders")]),
           ("Hafta 3: Sıralama", [])]
    return course_html(11, "Örnek Algoritmalar (Ayşe DENEME)", sec)


def test_parse_course_structure(html):
    c = us.parse_course(html)
    assert c["id"] == "11" and c["baslik"] == "Örnek Algoritmalar" and c["ogretim_elemani"] == "Ayşe DENEME"
    assert [b["ad"] for b in c["bolumler"]] == ["Genel", "21 Eylül - 27 Eylül", "28 Eylül - 4 Ekim", "Hafta 3: Sıralama"]
    assert [b["tarih_araligi"] for b in c["bolumler"]] == ["", "21 Eylül - 27 Eylül", "28 Eylül - 4 Ekim", ""]
    w1 = c["bolumler"][1]["etkinlikler"]
    assert [(a["id"], a["tur"]) for a in w1] == [("111", "resource"), ("112", "folder"), ("113", "assign")]   # tekilleştirildi
    assert w1[0]["ad"] == "1. Giriş & Temeller" and w1[0]["url"].endswith("/mod/resource/view.php?id=111")
    kinds = {a["tur"] for b in c["bolumler"] for a in b["etkinlikler"]}
    assert kinds == {"forum", "resource", "folder", "assign", "label", "page", "url", "choice", "lesson"}


def test_parse_assign_dates_and_descriptions(html):
    c = us.parse_course(html)
    assign = c["bolumler"][1]["etkinlikler"][2]
    assert ("Son yükleme tarihi", "Salı, 6 Ekim 2026, 12:00 AM") in assign["tarihler"]
    dt, raw = us.due_of(assign["tarihler"])
    assert dt == datetime(2026, 10, 6, 0, 0) and "6 Ekim" in raw                 # açılış tarihi teslim sayılmaz
    label = c["bolumler"][2]["etkinlikler"][0]
    assert "Değerli öğrenciler" in label["aciklama"] and "- Ödev değerlendirildi" in label["aciklama"]
    assert us.clean_ext(label["aciklama"]).count("<!--") == 0                    # dış metindeki sb:auto işaretçisi etkisizleşir
    assert "Bölüm 1: Giriş" in c["bolumler"][2]["etkinlikler"][1]["aciklama"]


def test_empty_or_garbage_html_is_safe():
    c = us.parse_course("<html>boş</html>")
    assert c["bolumler"] == [] and c["baslik"] == ""


@pytest.mark.parametrize("s,exp", [("Salı, 6 Ekim 2026, 12:00 AM", datetime(2026, 10, 6, 0, 0)),
                                   ("Pazartesi, 12 Ocak 2027, 11:59 PM", datetime(2027, 1, 12, 23, 59)),
                                   ("6 Ağustos 2026 23:59", datetime(2026, 8, 6, 23, 59)), ("yok", None)])
def test_parse_tr_datetime(s, exp):
    assert us.parse_tr_datetime(s) == exp


def test_course_matching_ignores_case_turkish_and_ve():
    cands = [{"kod": "ABC101", "ad": "Sinyaller ve Sistemler"}, {"kod": "ABC102", "ad": "Matematik I"},
             {"kod": "ABC103", "ad": "Ayrık Matematik"}]
    assert us.match_course("SİNYALLER SİSTEMLER", cands)["kod"] == "ABC101"
    assert us.match_course("Sinyaller & Sistemler", cands)["kod"] == "ABC101"
    assert us.match_course("matematik ı", cands)["kod"] == "ABC102"
    assert us.match_course("Ayrik Matematik", cands)["kod"] == "ABC103"
    assert us.match_course("Bilinmeyen Konular", cands) is None


def test_safe_name_blocks_traversal_and_obsidian_chars():
    assert us.safe_name("../../etc/passwd") == "passwd"
    assert us.safe_name("a[b]#c^d.pdf") == "a_b__c_d.pdf"
    assert us.safe_name("CON") != "CON" and us.safe_name("")
    assert len(us.safe_name("x" * 300 + ".pdf")) <= 120 and us.safe_name("x" * 300 + ".pdf").endswith(".pdf")


def test_html_to_text_keeps_links_and_drops_scripts():
    t = us.html_to_text('<script>evil()</script><p>Merhaba <a href="https://x.example/a">bağlantı</a></p><ul><li>bir</li><li>iki</li></ul>')
    assert "evil" not in t and "bağlantı (https://x.example/a)" in t and "- bir" in t and "- iki" in t
