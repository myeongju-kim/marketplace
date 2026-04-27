# 예시

## 입력

```bash
./scripts/tia-impact.sh \
  https://github.com/myeongju-kim/sample/pull/12 \
  ./references/domain-context.md
```

도메인 파일 없이도 실행할 수 있습니다.

```bash
./scripts/tia-impact.sh https://github.com/myeongju-kim/sample/pull/12
```

## 도메인 설명 예시

```md
## 1. 핵심 도메인
- 도메인명: 주문 결제
- 한 줄 설명: 결제 승인 이후 주문 상태와 후속 처리 상태를 확정한다.
- 이번 변경과 가장 밀접한 업무 흐름: 결제 성공 후 주문 완료 처리
```

## 변경 예시

```text
src/main/java/com/example/order/PaymentService.java
```

## 스크립트 분석 결과 예시

```text
변경 클래스 후보:
- PaymentService

역방향 Call Graph 후보:
- OrderService
- OrderController

DI 영향 후보:
- PaymentService를 주입받는 OrderService
- OrderService를 주입받는 OrderController
```

## AI 최종 판단 예시

```md
# TIA 테스트케이스

### 변경 요약
- `PaymentService`의 결제 처리 로직이 변경되었습니다.

### 도메인 매핑
- `PaymentService` -> 결제 승인/실패 분기
- `OrderService` -> 주문 상태 변경

### 영향받는 컴포넌트
- `PaymentService`
- `OrderService`
- `OrderController`

### 테스트케이스 목록
| ID | 구분 | 시나리오 | 사전조건 | 절차 | 기대결과 |
|---|---|---|---|---|---|
| TC-01 | 단위 | 결제 성공 응답 처리 | 승인 응답 mock 준비 | 1. 승인 응답 전달<br>2. 상태값 확인 | 결제 상태가 성공으로 저장된다 |
| TC-02 | 통합 | 결제 성공 후 주문 완료 처리 | 결제 가능한 주문 생성 | 1. 결제 요청<br>2. 승인 응답 처리<br>3. 주문 조회 | 주문 상태가 `PAID`로 변경되고 후속 처리 이벤트가 발생한다 |

### 제외한 테스트
- 단순 메시지 포맷 검증은 이번 변경 리스크가 낮아 제외

### 리스크 메모
- 결제 성공 후 적립/알림 분기가 같이 묶여 있다면 회귀 영향이 생길 수 있음

### 가정
- 도메인 설명 파일이 없었다면 `PaymentService`와 `OrderService` 명칭을 기반으로 결제 후 주문 완료 흐름을 추정했음
```
