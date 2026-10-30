---
type: ders
status: aktif
tags: [ders]
source: manual
source_id:
created: {{date}}
updated: {{date}}
due:
code:
semester: 2026-Guz
instructor:
schedule:
---
# {{title}}

## Teslimler ve sınavlar
```base
filters:
  and:
    - 'type == "teslim"'
    - file.hasLink(this.file)
views:
  - type: table
    name: Teslimler
    order: [file.name, kind, due, due_time, status]
    sort:
      - property: due
        direction: ASC
```

## Notlar
