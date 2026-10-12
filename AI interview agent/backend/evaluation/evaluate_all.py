"""Run both evaluations and write the canonical M2 evaluation report."""
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    runpy.run_path(str(Path(__file__).with_name("evaluate_retrieval.py")), run_name="__main__")
    runpy.run_path(str(Path(__file__).with_name("evaluate_matching.py")), run_name="__main__")
    retrieval = json.loads((ROOT / "data" / "retrieval_evaluation.json").read_text(encoding="utf-8"))
    matching = json.loads((ROOT / "data" / "matching_evaluation.json").read_text(encoding="utf-8"))
    report = {"retrieval": retrieval["retrieval"], "matching": matching["matching"]}
    (ROOT / "data" / "evaluation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
