# workflow

## 1. 입력 준비

사용자가 PR 주소를 전달합니다. 도메인 설명 파일은 선택입니다.

도메인 설명 파일이 필요하면 템플릿을 복사해서 채웁니다.

```bash
cp ./skills/test-impact-analysis/references/domain-context.template.md \
   ./skills/test-impact-analysis/references/domain-context.md
```

그 다음 다음 명령을 실행합니다.

```bash
./skills/test-impact-analysis/scripts/tia-impact.sh <PR_URL> [DOMAIN_FILE]
```

현재 위치가 스킬 디렉터리라면 다음처럼 실행합니다.

```bash
./scripts/tia-impact.sh <PR_URL> ./references/domain-context.md
```

도메인 파일 없이 실행하는 예시는 다음과 같습니다.

```bash
./scripts/tia-impact.sh <PR_URL>
```

## 2. 분석 리포트 확인

스크립트 실행 후 생성되는 파일을 확인합니다.

```bash
cat tia-report.md
```

## 3. 영향 컴포넌트 해석

리포트에서 다음 항목을 우선 확인합니다.

- 변경 파일
- 변경 클래스 후보
- 변경 메서드 후보
- 역방향 Call Graph 후보
- Spring DI 영향 후보
- Mapper / Repository 참조 후보

## 4. 도메인 매핑

AI는 `tia-report.md`와 도메인 설명 파일이 있으면 함께 읽고 다음을 먼저 연결합니다.

- 변경 클래스/메서드 -> 실제 업무 단계
- 영향 컴포넌트 -> 사용자 시나리오 또는 배치 시나리오
- 예외 흐름 -> 실패/롤백/중복 처리 검증 포인트

도메인 설명 파일이 없으면 다음 대체 기준을 사용합니다.

- 클래스명/메서드명에서 업무 동사 추정
- Controller-Service-Repository 연결로 사용자 흐름 추정
- Scheduler/Batch/Publisher 명칭으로 비동기 흐름 추정

## 5. 테스트케이스 생성

AI는 다음 기준으로 `tia-test-cases.md`를 작성합니다.

### 기본 규칙

- `OrderService` 변경 → `OrderServiceTest`
- `OrderController` 영향 → `OrderControllerTest`
- Repository / Mapper 변경 → Repository 테스트 또는 관련 Service 테스트
- 결제, 주문, 정산, 약정 등 주요 도메인 흐름 변경 → Integration Test 포함 검토

### 의미 기반 규칙

- 단순 포맷 변경이면 단위 테스트 위주로 제한합니다.
- 상태 전이, 금액, 정산, 결제, 권한, 외부 연동 변경은 통합 테스트를 포함합니다.
- 이벤트 발행, 스케줄러, 배치 흐름은 회귀 테스트 후보에 포함합니다.

### 문서화 규칙

- 각 테스트케이스는 사람이 직접 수행 가능한 절차를 포함합니다.
- 각 테스트케이스는 사전조건과 기대결과를 반드시 포함합니다.
- 단위 테스트 추천만 적고 끝내지 말고, 왜 이 테스트가 필요한지 도메인 관점 이유를 씁니다.
- 도메인 설명이 없으면 추정 기반 시나리오라는 점을 문서에 명시합니다.
- 리스크가 낮은 후보는 별도 제외 섹션으로 분리합니다.

## 6. 최종 산출물 작성

최종 산출물은 `tia-test-cases.md` 파일입니다.

```md
# TIA 테스트케이스

## 변경 요약
이번 변경은 `PaymentService`의 결제 처리 흐름에 영향을 줍니다.

## 도메인 매핑
- `PaymentService.pay()` -> 결제 승인 이후 주문 상태 변경
- `OrderService.completePayment()` -> 후속 적립/알림 분기

## 테스트케이스 목록
| ID | 구분 | 시나리오 | 사전조건 | 절차 | 기대결과 |
|---|---|---|---|---|---|
| TC-01 | 통합 | 결제 성공 후 주문 완료 처리 | 결제 가능한 주문 생성 | 1. 결제 요청<br>2. 승인 응답 처리 | 주문 상태가 `PAID`로 변경되고 후속 처리 수행 |
```

## 7. 판단 기준

테스트 후보는 다음 순서로 좁힙니다.

1. 변경 클래스 직접 테스트
2. 변경 클래스를 호출하는 상위 컴포넌트 테스트
3. 변경 컴포넌트가 포함된 도메인 통합 테스트
4. 리스크가 낮은 후보 제거
