"""Exercise the semantic verifier on two supported pairs and a numeric negative control."""
import copy
import json
from pathlib import Path

from app.validation import validate_items

event = json.loads(Path("/artifacts/local-model/event.json").read_text(encoding="utf-8"))
items = copy.deepcopy(event["result"]["items"][:2])
negative = copy.deepcopy(items[1])
negative["id"] = "synthetic-numeric-negative-control"
negative["answer_en"] = negative["answer_en"].replace("120", "999")
items.append(negative)
validated = validate_items(items, event["result"]["evidence"])
summary = [{"id": i["id"], "grounded": i["grounded"], "equivalent": i["pt_en_equivalent"], "reason": i["review_reason"], "validation": i["validation"]} for i in validated]
Path("/artifacts/local-model/verifier-check.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
assert not validated[-1]["grounded"] and not validated[-1]["pt_en_equivalent"]
print(json.dumps(summary, ensure_ascii=False), flush=True)
