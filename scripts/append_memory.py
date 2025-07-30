import sys
from datetime import datetime

message = sys.argv[1]
filepath = sys.argv[2] if len(sys.argv) > 2 else "gpt_memory_log.md"

entry = f"\n\n---\n\n### 🕒 {datetime.utcnow().isoformat()} UTC\n{message}"

with open(filepath, "a", encoding="utf-8") as f:
    f.write(entry)
