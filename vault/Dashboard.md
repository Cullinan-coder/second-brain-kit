---
type: dashboard
tags: [dashboard]
---
# Dashboard

[[00-Inbox/onay-bekleyenler|Onay bekleyenler]] · [[_system/PLAN|Plan]] · [[CLAUDE|Kurallar]]

## Bu hafta
```base
filters:
  and:
    - 'status != "tamamlandi" && status != "yapildi" && status != "iptal"'
    - 'due >= today()'
    - 'due <= today() + "7d"'
    - '!file.inFolder("_templates")'
views:
  - type: table
    name: Bu hafta
    order: [file.name, type, kind, due, due_time, status]
    sort:
      - property: due
        direction: ASC
```

## Gecikenler
```base
filters:
  and:
    - 'status == "acik" || status == "planlandi" || status == "hazirlaniyor"'
    - 'due < today()'
    - 'type != "gunluk"'
    - '!file.inFolder("_templates")'
views:
  - type: table
    name: Gecikenler
    order: [file.name, type, due, status]
    sort:
      - property: due
        direction: ASC
```

## Önümüzdeki 30 gün
```base
filters:
  and:
    - 'type != "gunluk"'
    - 'status != "tamamlandi" && status != "yapildi" && status != "iptal"'
    - 'due > today() + "7d"'
    - 'due <= today() + "30d"'
    - '!file.inFolder("_templates")'
views:
  - type: table
    name: 30 gün
    order: [file.name, type, kind, due, status]
    sort:
      - property: due
        direction: ASC
```

## Açık başvurular
```base
filters:
  and:
    - 'type == "basvuru"'
    - 'status != "kabul" && status != "red" && status != "vazgecildi"'
    - '!file.inFolder("_templates")'
views:
  - type: table
    name: Başvurular
    order: [file.name, kind, organizer, due, status]
    sort:
      - property: due
        direction: ASC
```

## Aktif projeler
```base
filters:
  and:
    - 'type == "proje"'
    - 'status == "aktif"'
    - '!file.inFolder("_templates")'
views:
  - type: table
    name: Projeler
    order: [file.name, area, repo, updated]
    sort:
      - property: updated
        direction: DESC
```

## Inbox
```base
filters:
  and:
    - 'file.inFolder("00-Inbox")'
    - 'file.ext == "md"'
views:
  - type: list
    name: Inbox
    order: [file.name, file.mtime]
```
