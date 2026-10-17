"""Independent source arithmetic and packaged slide/frame checks for this lesson."""
import argparse
import hashlib
import json
import re
from fractions import Fraction
from pathlib import Path
from zipfile import ZipFile

from lxml import etree as E
from PIL import Image

ROOT = Path(__file__).resolve().parent
NS = {"a":"http://schemas.openxmlformats.org/drawingml/2006/main",
      "p":"http://schemas.openxmlformats.org/presentationml/2006/main"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run")
    args = parser.parse_args()
    run = ROOT / "tmp/tutorial_base/tutorial3/methods-work" / args.run
    source = {-1:0, 0:0, 1:2, 2:4, 3:2, 4:0}
    expected = [Fraction(source[n] + source[n-1], 2) for n in range(5)]
    assert expected == [0, 1, 3, 3, 1]
    checks = []

    def passed(name, evidence):
        checks.append({"check":name, "status":"pass", "evidence":evidence})

    passed("Independent exact arithmetic", [str(v) for v in expected])
    numerical = json.loads((run / "demos-check.json").read_text())["numerical"]
    assert numerical["input"] == [source[n] for n in range(5)]
    assert numerical["previous"] == source[-1]
    assert numerical["output"] == expected
    for row in numerical["rows"]:
        n = row["n"]
        assert (row["previous"],row["current"],row["sum"],row["mean"]) == (source[n-1],source[n],source[n]+source[n-1],expected[n])
    passed("Every generated arithmetic row", numerical["rows"])

    with ZipFile(run / "candidate.pptx") as deck:
        slides = [name for name in deck.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml",name)]
        assert len(slides) == 6
        xml = E.fromstring(deck.read("ppt/slides/slide5.xml"))
        tables = xml.findall(".//a:tbl", NS)
        assert len(tables) == 1
        rows = [["".join(cell.itertext()) for cell in row.findall("a:tc",NS)] for row in tables[0].findall("a:tr",NS)]
        assert rows[0] == ["n","Previous","Current","Average","Output"]
        for n, row in enumerate(rows[1:]):
            assert row == [str(n),str(source[n-1]),str(source[n]),f"({source[n]} + {source[n-1]}) / 2",str(expected[n])]
        texts = " ".join(" ".join(E.fromstring(deck.read(s)).xpath("//a:t/text()",namespaces=NS)) for s in slides)
        assert not re.search(r"ELEG|PAM|runbang@|Tutorial [345]|Modulation|Demodulation",texts)
        passed("Actual PPTX native table", {"rows":len(rows)-1,"columns":len(rows[0]),"complete":True})
        passed("Actual PPTX scope and visible identity", {"slides":len(slides),"courseTextLeakage":False})

    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["genericContent"] is True and manifest["note7Aligned"] is False
    assert all(link["target"] == "overview" for link in manifest["links"])
    passed("Navigation meaning", "All six title links return to the input overview, slide 1.")
    equations = {e["name"]:e["tex"] for e in manifest["equations"]}
    rule = r"y[n]=\frac{x[n]+x[n-1]}{2}"
    assert equations["general-rule"] == equations["takeaway-rule"] == rule
    assert equations["one-pair-answer"] == r"y[2]=\frac{4+2}{2}=3"
    assert equations["all-outputs"] == equations["worked-answer"] == r"y[0..4]=[0,1,3,3,1]"
    passed("Equation identity and substitution", "Rule, n=2 substitution, and both output vectors match the source.")

    for demo in ("pair-to-output","moving-window"):
        folder = run / "demos" / demo
        meta = json.loads((folder / "frames.json").read_text())
        assert len(meta["frames"]) == len(meta["durations"]) == len(meta["states"])
        assert (folder / "first.png").read_bytes() == (folder / meta["frames"][0]).read_bytes()
        assert (folder / "last.png").read_bytes() == (folder / meta["frames"][-1]).read_bytes()
        for frame in meta["frames"]:
            with Image.open(folder / frame) as image:
                assert image.size == (2240,500)
        if demo == "pair-to-output":
            states = meta["states"]
            assert not states[0]["outputVisible"] and states[-1]["outputVisible"]
            assert states[0]["movingHeights"] == [2,4]
            assert states[-1]["movingHeights"] == [3,3]
            for state in states:
                a,b = state["movingHeights"]
                assert abs(a+b-6)<1e-12 and 2<=a<=3 and 3<=b<=4
            with Image.open(folder / "last.png") as image:
                assert max(image.convert("RGB").getpixel((1800,268)))<60
            with Image.open(folder / "first.png") as image:
                assert min(image.convert("RGB").getpixel((1800,268)))>245
            passed("Actual pair output pixels", "Index 2 has no output on entry and a black point at height 3 in the held result.")
            passed("Every pair interpolation state", {"states":len(states),"constantSum":6,"finalMean":3})
        else:
            previous_outputs=[]
            observed = set()
            for state in meta["states"]:
                count=len(state["outputs"])
                assert state["outputs"] == expected[:count]
                assert state["outputs"][:len(previous_outputs)] == previous_outputs
                assert count>=len(previous_outputs)
                if not state["moving"]:
                    n=state["segment"]
                    assert state["selectedIndices"] == [n-1,n]
                    assert state["selectedValues"] == [source[n-1],source[n]]
                    observed.add(n)
                previous_outputs=state["outputs"]
            assert observed == set(range(5)) and previous_outputs == expected
            with Image.open(folder / "last.png") as image:
                image=image.convert("RGB")
                for n,v in enumerate(expected):
                    px,py=2*(740+n*80),2*(200-22*int(v))
                    assert max(image.getpixel((px,py)))<60
            passed("Actual final output pixels", "All five black output points are at independently calculated index/height coordinates.")
            passed("Every moving-pair state", {"states":len(meta["states"]),"indices":sorted(observed),"priorOutputsRetained":True,"futureInputAssumed":False})

    report={"status":"pass","candidateSha256":hashlib.sha256((run/"candidate.pptx").read_bytes()).hexdigest(),"checks":checks,"nativePlaybackTested":False,"teachingApproved":False}
    (run/"topic-check.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"status":"pass","checks":len(checks),"file":str(run/"topic-check.json")}))


if __name__ == "__main__":
    main()
