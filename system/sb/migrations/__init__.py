"""Kasa şema göçleri: `m0002_<ad>.py`, `m0003_<ad>.py` ... sıralı modüller.

Her modül şunları tanımlar:
- `VERSION: int`      — göç bitince kasanın ulaşacağı şema sürümü (dosya numarasıyla aynı, ardışık).
- `DESCRIPTION: str`  — tek satır, kullanıcıya gösterilir.
- `up(vault: Path, dry_run: bool) -> list[str]` — yapılan/yapılacak değişikliklerin listesi.
  İdempotent olmalı (ikinci çalıştırma boş liste döner), `dry_run=True` iken hiçbir şey yazmamalı,
  yalnız git tarafından İZLENEN dosyalara dokunmalı (geri alma git ile yapılır) ve sürüm damgasını kendisi yazmamalı
  (`sb.schema` yazar). Hata durumunda istisna fırlatmalı.
"""
