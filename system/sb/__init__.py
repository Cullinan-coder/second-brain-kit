"""Second Brain araçları."""
import os

# sb'nin başlattığı `claude -p` alt süreçleri (derleme, tarih çıkarma) Claude Code hafıza kancalarını tetiklemesin:
# tools/cc_hook.py bu değişkeni görünce hiçbir şey enjekte etmez.
os.environ.setdefault("SB_NO_HOOK", "1")
