# Görev ve planlama

> Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.

| | |
|---|---|
| Modül kimliği | `tasks_plan` |
| Kategori | Verimlilik ve iletişim |
| Varsayılan | açık |
| Madde sayısı | 14 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.

Bu modül özellik kataloğundan **14 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Görev ve planlama`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Öğrenci seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Bugün planı**, **Görev panosu** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [162](#madde-162) | Görev panosu (kanban) | hazır | 0.7.0 |
| [163](#madde-163) | Akıllı günlük plan | hazır | 0.7.0 |
| [165](#madde-165) | Pomodoro / odak modu | hazır | 0.7.0 |
| [166](#madde-166) | Alışkanlık takibi | hazır | 0.7.0 |
| [167](#madde-167) | Hedefler (OKR) | hazır | 0.7.0 |
| [168](#madde-168) | Haftalık gözden geçirme sihirbazı | hazır | 0.7.0 |
| [169](#madde-169) | Tekrarlayan görevler | hazır | 0.7.0 |
| [170](#madde-170) | Bağımlı görevler | hazır | 0.7.0 |
| [171](#madde-171) | Mail → görev | hazır | 0.7.0 |
| [172](#madde-172) | Toplantı hazırlık notu | hazır | 0.7.0 |
| [173](#madde-173) | Toplantı sonrası karar/görev çıkarma | hazır | 0.7.0 |
| [175](#madde-175) | Enerji/ruh hali ile plan uyarlama | hazır | 0.7.0 |
| [176](#madde-176) | Akıllı hatırlatma zamanı | hazır | 0.7.0 |
| [179](#madde-179) | Bugün en önemli 3 iş | hazır | 0.7.0 |

<a id="madde-162"></a>

### 162. Görev panosu (kanban)

- **Ne işe yarar:** «Görev panosu (kanban)» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-163"></a>

### 163. Akıllı günlük plan

- **Ne işe yarar:** «Akıllı günlük plan» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-165"></a>

### 165. Pomodoro / odak modu

- **Ne işe yarar:** «Pomodoro / odak modu» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-166"></a>

### 166. Alışkanlık takibi

- **Ne işe yarar:** «Alışkanlık takibi» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-167"></a>

### 167. Hedefler (OKR)

- **Ne işe yarar:** «Hedefler (OKR)» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-168"></a>

### 168. Haftalık gözden geçirme sihirbazı

- **Ne işe yarar:** «Haftalık gözden geçirme sihirbazı» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-169"></a>

### 169. Tekrarlayan görevler

- **Ne işe yarar:** «Tekrarlayan görevler» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-170"></a>

### 170. Bağımlı görevler

- **Ne işe yarar:** «Bağımlı görevler» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-171"></a>

### 171. Mail → görev

- **Ne işe yarar:** «Mail → görev» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-172"></a>

### 172. Toplantı hazırlık notu

- **Ne işe yarar:** «Toplantı hazırlık notu» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-173"></a>

### 173. Toplantı sonrası karar/görev çıkarma

- **Ne işe yarar:** «Toplantı sonrası karar/görev çıkarma» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-175"></a>

### 175. Enerji/ruh hali ile plan uyarlama

- **Ne işe yarar:** «Enerji/ruh hali ile plan uyarlama» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-176"></a>

### 176. Akıllı hatırlatma zamanı

- **Ne işe yarar:** «Akıllı hatırlatma zamanı» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).

<a id="madde-179"></a>

### 179. Bugün en önemli 3 iş

- **Ne işe yarar:** «Bugün en önemli 3 iş» (Görev, takvim ve verimlilik kategorisi), «Görev ve planlama» modülünün parçasıdır. Modülün amacı: Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Görev ve planlama» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bugün planı**, **Görev panosu**; komut: [`sb plan`](../14-komut-referansi.md#sb-plan), [`sb tasks-board`](../14-komut-referansi.md#sb-tasks-board), [`sb task`](../14-komut-referansi.md#sb-task).
