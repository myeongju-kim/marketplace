# kingmj-skills-marketplace

개인 전용 AI 스킬 마켓플레이스입니다.

이 저장소는 Git URL 기반으로 스킬을 배포하는 용도로 구성되어 있습니다. 각 스킬은 순수 Markdown 구조를 사용하므로 특정 벤더 전용 포맷에 묶이지 않고 여러 에이전트가 공통으로 읽을 수 있습니다.

## 설치 예시

```bash
npx skills add https://github.com/myeongju-kim/marketplace.git --skill test-driven-development
```

## 스킬 규칙

각 스킬은 다음 구조를 따릅니다.

```text
skills/<skill-name>/
├─ SKILL.md
├─ workflow.md
├─ checklist.md
└─ examples/
```

### `SKILL.md`
- YAML frontmatter 포함
- 스킬 이름과 설명 정의
- 사용 상황, 실행 순서, 운영 규칙 명시

기본 예시:

```md
---
name: test-driven-development
description: Use this skill when the user wants implementation to follow a strict test-first workflow.
---

# test-driven-development

## 사용 상황
- 테스트 우선 개발이 필요할 때

## 실행 순서
1. 실패 테스트를 먼저 작성합니다.
2. 최소 구현으로 테스트를 통과시킵니다.
```

## manifest.json

루트의 `manifest.json`은 설치 도구나 인덱서가 스킬 목록을 읽기 위한 메타데이터입니다.

포함 정보:
- 마켓플레이스 이름
- 설명
- 저장소 내 스킬 목록
- 각 스킬의 경로와 파일 구성

## 현재 포함된 스킬

- `test-driven-development`: 테스트 우선 개발을 강제하는 스킬

## 호환성 원칙

- 특정 벤더 전용 포맷에 의존하지 않음
- 순수 Markdown + JSON 메타데이터만 사용
- 여러 에이전트가 직접 읽고 실행 절차를 따를 수 있도록 구성

## License

This repository is licensed under the terms in the [LICENSE](LICENSE) file.
