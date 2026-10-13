"""Collect local POC evidence without modifying or approving any event."""
import argparse
import json
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("event_id")
parser.add_argument("--output", default="artifacts")
args = parser.parse_args()
folder = Path(args.output)
folder.mkdir(parents=True, exist_ok=True)


def get(path):
    req = urllib.request.Request("http://127.0.0.1:8080/api" + path, headers={"X-SimplFAQ": "local-poc"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


event = json.loads(get("/events/" + args.event_id))
(folder / "sample-event.json").write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": event["status"], "stage": event["runs"][0]["stage"], "error": event["error"]}, ensure_ascii=False))
if event["result"]:
    (folder / "sample-faq.docx").write_bytes(get("/events/" + args.event_id + "/document"))
    print(json.dumps({"items": len(event["result"]["items"]), "metrics": event["result"]["metrics"],
                      "gaps": event["result"]["gaps"], "conflicts": event["result"]["conflicts"]}, ensure_ascii=False))
    for item in event["result"]["items"]:
        print(json.dumps({k: item[k] for k in ["question_pt", "answer_pt", "question_en", "answer_en", "grounded", "pt_en_equivalent", "review_reason"]}, ensure_ascii=False))
