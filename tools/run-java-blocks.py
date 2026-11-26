"""Run every runnable Java block (first line `// Run: ClassName.java`) found in markdown notes.

Each block is written to <workdir>/<note-name>/<NN>-<ClassName>/ and run with `java ClassName.java`
(plus any flags given as `// Run: X.java  (needs: java --flag X.java)`). Prints one summary line per note and
details only for blocks that exit non-zero. A few blocks exit non-zero ON PURPOSE (an OutOfMemoryError demo,
a System.exit demo), so read the failure before assuming something is broken.

Usage (needs JDK 21 and Python 3):
    python tools/run-java-blocks.py <workdir> <note.md> [<note.md> ...]
Example:
    python tools/run-java-blocks.py /tmp/blocks 02-languages/java/02-collections/03-hashmap-internals.md
Use a <workdir> OUTSIDE the repo so build output and heap dumps are not committed."""
import re, subprocess, sys, pathlib, shutil

work = pathlib.Path(sys.argv[1])
total = passed = 0
failures = []
for md_path in sys.argv[2:]:
    md = pathlib.Path(md_path)
    text = md.read_text(encoding="utf-8")
    blocks = re.findall(r"```java\n(// Run: .*?)\n(.*?)```", text, re.S)
    p = f = 0
    for i, (first, body) in enumerate(blocks, 1):
        m = re.search(r"// Run: (\w+)\.java", first)
        name = m.group(1)
        flags = []
        n = re.search(r"needs: java (.*?) \w+\.java", first)
        if n:
            flags = n.group(1).split()
        d = work / md.stem / f"{i:02d}-{name}"
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        (d / f"{name}.java").write_text(first + "\n" + body, encoding="utf-8")
        total += 1
        try:
            r = subprocess.run(["java", *flags, f"{name}.java"], cwd=d, capture_output=True, text=True, timeout=120)
            ok = r.returncode == 0
            detail = (r.stderr or r.stdout)[-500:]
        except subprocess.TimeoutExpired:
            ok, detail = False, "TIMEOUT after 120 s"
        if ok:
            p += 1; passed += 1
        else:
            f += 1
            failures.append((md.name, i, name, flags, detail.strip()))
    print(f"{md.name}: {p} passed, {f} failed, {len(blocks)} blocks")
print(f"\nTOTAL {passed}/{total} passed")
for md, i, name, flags, detail in failures:
    print(f"\n--- FAIL {md} block #{i} {name} flags={flags}\n{detail}")
