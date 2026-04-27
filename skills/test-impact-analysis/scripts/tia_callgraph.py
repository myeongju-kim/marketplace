#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
from pathlib import Path
from collections import defaultdict

JAVA_CLASS_RE = re.compile(r'\b(class|interface|enum|record)\s+([A-Za-z_][A-Za-z0-9_]*)')
METHOD_RE = re.compile(r'(public|protected|private|static|\s)+[\w<>\[\], ?]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
ANNOTATION_COMPONENT_RE = re.compile(r'@(Service|Component|Repository|Controller|RestController|Mapper|Configuration)\b')
FIELD_INJECTION_RE = re.compile(r'@(Autowired|Resource|Inject)[\s\S]{0,120}?\b([A-Z][A-Za-z0-9_]*)\s+([a-zA-Z_][A-Za-z0-9_]*)\s*;')
CONSTRUCTOR_PARAM_RE = re.compile(r'\(([^)]*)\)')
TYPE_RE = re.compile(r'\b([A-Z][A-Za-z0-9_]*(?:Service|Repository|Mapper|Client|Controller|Handler|Publisher|Reader|Writer|Processor|Scheduler|Batch))\b')

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp949", errors="ignore")
    except Exception:
        return ""

def find_java_files(root: Path):
    excludes = {".git", "build", "target", ".gradle", ".idea", "node_modules", "out"}
    for p in root.rglob("*.java"):
        if any(part in excludes for part in p.parts):
            continue
        yield p

def extract_class_name(text: str, fallback: str):
    m = JAVA_CLASS_RE.search(text)
    return m.group(2) if m else fallback

def extract_methods(text: str):
    methods = []
    for m in METHOD_RE.finditer(text):
        name = m.group(2)
        if name not in {"if", "for", "while", "switch", "catch", "return", "new"}:
            methods.append(name)
    return sorted(set(methods))

def extract_referenced_types(text: str):
    return sorted(set(TYPE_RE.findall(text)))

def is_component(text: str):
    return bool(ANNOTATION_COMPONENT_RE.search(text))

def analyze(root: Path, diff_file: Path):
    changed_files = [line.strip() for line in read_text(diff_file).splitlines() if line.strip()]
    changed_java_files = [f for f in changed_files if f.endswith(".java") and "/test/" not in f and "\\test\\" not in f]

    class_by_file = {}
    file_by_class = {}
    methods_by_class = {}
    refs_by_class = defaultdict(set)
    component_classes = set()

    for path in find_java_files(root):
        text = read_text(path)
        cls = extract_class_name(text, path.stem)
        rel = str(path.relative_to(root))
        class_by_file[rel] = cls
        file_by_class[cls] = rel
        methods_by_class[cls] = extract_methods(text)
        refs_by_class[cls].update(extract_referenced_types(text))
        if is_component(text):
            component_classes.add(cls)

    changed_classes = []
    changed_methods = defaultdict(list)

    for rel in changed_java_files:
        path = root / rel
        if not path.exists():
            continue
        text = read_text(path)
        cls = extract_class_name(text, Path(rel).stem)
        changed_classes.append(cls)
        changed_methods[cls] = extract_methods(text)

    changed_classes = sorted(set(changed_classes))

    # 역방향 참조: 변경 클래스를 참조하는 클래스
    upstream = defaultdict(set)
    for cls, refs in refs_by_class.items():
        for changed in changed_classes:
            if changed in refs:
                upstream[changed].add(cls)

    # DI 후보: Service/Repository/Mapper/Controller 타입 참조 기준
    di_candidates = defaultdict(set)
    for cls, refs in refs_by_class.items():
        for changed in changed_classes:
            if changed in refs and cls in component_classes:
                di_candidates[changed].add(cls)

    # 영향 컴포넌트: 변경 클래스 + 상위 호출/참조 후보 + DI 후보
    impacted = set(changed_classes)
    for s in upstream.values():
        impacted.update(s)
    for s in di_candidates.values():
        impacted.update(s)

    # 테스트 후보: 이름 기반
    test_candidates = set()
    all_classes = set(file_by_class.keys())
    for cls in impacted:
        for suffix in ["Test", "Tests", "IT", "IntegrationTest"]:
            candidate = f"{cls}{suffix}"
            if candidate in all_classes:
                test_candidates.add(candidate)
        # 도메인/상위 흐름 테스트 후보
        base = re.sub(r'(Service|Controller|Repository|Mapper|Client|Handler|Scheduler|Batch)$', '', cls)
        for test_cls in all_classes:
            if "Test" in test_cls or test_cls.endswith("IT"):
                if base and base in test_cls:
                    test_candidates.add(test_cls)

    return {
        "changed_files": changed_files,
        "changed_java_files": changed_java_files,
        "changed_classes": changed_classes,
        "changed_methods": changed_methods,
        "upstream": {k: sorted(v) for k, v in upstream.items()},
        "di_candidates": {k: sorted(v) for k, v in di_candidates.items()},
        "impacted": sorted(impacted),
        "test_candidates": sorted(test_candidates),
    }

def md_list(items):
    if not items:
        return "- 없음\n"
    return "\n".join(f"- `{x}`" for x in items) + "\n"

def write_report(data, args):
    domain_file = args.domain_file or ""
    domain_text = read_text(Path(domain_file)).strip() if domain_file else ""
    out = []
    out.append("# TIA 영향 분석 리포트\n")
    out.append("## 입력 정보\n")
    out.append(f"- PR 주소: {args.pr_url}\n")
    out.append(f"- Base: `{args.base_ref}`\n")
    out.append(f"- Head: `{args.head_ref}`\n\n")
    if domain_file:
        out.append(f"- 도메인 설명 파일: `{domain_file}`\n\n")
    else:
        out.append("- 도메인 설명 파일: 없음\n\n")

    out.append("## 도메인 설명\n")
    if domain_text:
        out.append("```md\n")
        out.append(domain_text)
        if not domain_text.endswith("\n"):
            out.append("\n")
        out.append("```\n\n")
    else:
        out.append("- 없음\n\n")

    out.append("## 변경 파일\n")
    out.append(md_list(data["changed_files"]))
    out.append("\n")

    out.append("## 변경 Java 파일\n")
    out.append(md_list(data["changed_java_files"]))
    out.append("\n")

    out.append("## 변경 클래스 후보\n")
    out.append(md_list(data["changed_classes"]))
    out.append("\n")

    out.append("## 변경 메서드 후보\n")
    if data["changed_methods"]:
        for cls, methods in data["changed_methods"].items():
            out.append(f"### `{cls}`\n")
            out.append(md_list(methods))
    else:
        out.append("- 없음\n")
    out.append("\n")

    out.append("## 역방향 Call Graph 후보\n")
    if data["upstream"]:
        for changed, callers in data["upstream"].items():
            out.append(f"### `{changed}`를 참조하는 클래스\n")
            out.append(md_list(callers))
    else:
        out.append("- 없음\n")
    out.append("\n")

    out.append("## Spring DI 영향 후보\n")
    if data["di_candidates"]:
        for changed, users in data["di_candidates"].items():
            out.append(f"### `{changed}`를 주입/참조하는 컴포넌트 후보\n")
            out.append(md_list(users))
    else:
        out.append("- 없음\n")
    out.append("\n")

    out.append("## 영향받는 컴포넌트 후보\n")
    out.append(md_list(data["impacted"]))
    out.append("\n")

    out.append("## 정적 규칙 기반 테스트 후보\n")
    out.append(md_list(data["test_candidates"]))
    out.append("\n")

    out.append("## AI에게 요청할 판단\n")
    out.append("""
아래 기준으로 최종 테스트케이스 문서(`tia-test-cases.md`)를 작성하세요.

1. 변경 클래스 직접 테스트를 우선 포함합니다.
2. 역방향 Call Graph / DI 후보 중 실제 비즈니스 흐름에 해당하는 테스트를 포함합니다.
3. 결제, 주문, 정산, 권한, 외부 연동, 상태 변경, 배치 변경은 Integration Test 포함을 검토합니다.
4. 단순 포맷, 로그, 메시지 변경은 과도한 테스트를 제외합니다.
5. 도메인 설명이 있으면 변경사항과 연결해 테스트 시나리오를 작성합니다.
6. 도메인 설명이 없으면 클래스명, 메서드명, 영향 컴포넌트 이름을 기준으로 시나리오를 추정하고, 반드시 가정과 저신뢰 구간을 적습니다.
7. 각 테스트케이스에 사전조건, 절차, 기대결과를 반드시 작성합니다.
8. 최종 답변 본문보다 파일 산출물 작성이 우선입니다.
""")

    Path(args.output).write_text("".join(out), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="PR 변경사항 기반 TIA 영향 분석 리포트를 생성합니다.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--diff-file", required=True)
    parser.add_argument("--pr-url", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--domain-file", required=False)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = analyze(Path(args.root), Path(args.diff_file))
    write_report(data, args)

if __name__ == "__main__":
    main()
