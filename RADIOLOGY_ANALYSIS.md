# 방사선 판독 결과 AI 분석 시스템 구현

## 개요
의료 정보 시스템에 **방사선 판독 결과(Radiology Report)** 분석 기능을 추가했습니다. 이 시스템은 LangGraph를 기반으로 한 의료 워크플로우에 방사선 분석 노드를 통합하여, 다른 임상 데이터(경과기록, 활력징후, 약물, 검사)와 함께 **종합 분석**을 제공합니다.

---

## 핵심 변경 사항

### 1. **RadiologyReport 모델 단순화**
방사선 판독 입력 데이터를 최소 필드로 정의:
```python
class RadiologyReport(TypedDict):
  ymd: str          # 검사일자
  time: str         # 검사시간
  modality: str     # 검사 종류 (X-ray, CT, MRI 등)
  examType: str     # 검사 부위 (흉부, 복부 등)
  findings: str   # 임상 소견
```

### 2. **의료 그래프에 3개 분석 노드 추가**
LangGraph의 `MedicalGraphState`에 방사선 분석 결과 필드 추가:
```python
radiology_summary: RadiologySummaryResult
radiology_progression: RadiologyProgressionResult
integrated_radiology_analysis: IntegratedClinicalAnalysisResult
```

### 3. **Loading 타입 확장**
로딩 상태에 새로운 타겟 추가:
```python
type LoadingCompleteTarget = Literal[
    "progress_notes", "ns_vs", "prescriptions", "labs",
    "radiology", "radiology_progression", "integrated_radiology"
]
```

---

## 아키텍처

### LangGraph Workflow 구조

```
                    ┌─ create_progressnote_summary ─┐
                    ├─ create_ns_vs_summary ────────┤
        START ───→  ├─ create_prescription_summary ─┼─→ END
                    ├─ create_lab_summary ──────────┤
                    ├─ create_radiology_summary ────┤
                    ├─ create_radiology_progression ┤
                    └─ create_integrated_radiology_analysis ┘
```

모든 노드는 **병렬 처리**됨 (START → 각 노드 → END)

---

## 분석 노드 설명

### 1. **create_radiology_summary** (단일 분석)
최신 방사선 검사에 대한 상세 분석:
- **입력**: 최신 RadiologyReport
- **출력**: `RadiologySummaryResult`
  - `main_finding`: 주요 소견
  - `clinical_significance`: 임상적 의미
  - `progression_analysis`: 질병 진행 (이전과 비교)
  - `urgent_findings`: 긴급 소견 리스트
  - `recommendations`: 권장 검사
  - `follow_up_plan`: 후속 계획
  - `clinical_opinion`: 임상의학적 의견

### 2. **create_radiology_progression** (비교 분석)
여러 방사선 검사의 시간 경과 분석:
- **입력**: 2개 이상의 RadiologyReport (시간순 정렬)
- **출력**: `RadiologyProgressionResult`
  - `overall_trend`: 호전/안정/악화
  - `key_changes`: 주요 변화 사항
  - `evolution_timeline`: 진행 타임라인
  - `predicted_outcome`: 예상 결과
  - `clinical_implications`: 임상적 의미
  - `recommended_follow_up`: 추적 계획

### 3. **create_integrated_radiology_analysis** (통합 분석)
방사선 + 활력징후 + 혈액검사 + 투약 종합 분석:
- **입력**: 모든 임상 데이터 통합
- **출력**: `IntegratedClinicalAnalysisResult`
  - `clinical_correlation_analysis`: 상관관계 분석
  - `overall_clinical_picture`: 전체 그림
  - `progression_assessment`: 진행 추이 및 예후
  - `integrated_clinical_opinion`: 통합 의견
  - `management_recommendations`: 관리 권고
  - `priority_actions`: 우선순위 조치
  - `risk_level`: 종합 위험도

---

## Socket.IO 이벤트

### summarize_patient (기존 - 개선됨)
**전체 환자 종합 분석** (방사선 포함)
```
클라이언트 → emit('summarize_patient', data)
서버 → 의료 그래프 워크플로우 실행 (모든 노드 병렬 처리)
서버 → emit_with_ack('summarize_patient', response)
```

**응답 데이터**:
```typescript
{
  progressNotesSummary: ProgressNoteResult,
  vsNsSummary: VsNsSummaryResult,
  prescriptionSummary: PrescriptionSummaryResult,
  labSummary: LabSummaryResult,
  radiologySummary?: RadiologySummaryResult,
  radiologyProgression?: RadiologyProgressionResult,
  integratedRadiologyAnalysis?: IntegratedClinicalAnalysisResult
}
```

### query_radiology_analysis (신규)
**방사선 분석만 단독 쿼리**
```
클라이언트 → emit('query_radiology_analysis', data)
서버 → 의료 그래프 워크플로우 실행
서버 → 방사선 결과만 추출
서버 → emit_with_ack('query_radiology_analysis', response)
```

**응답 데이터**:
```typescript
{
  radiologySummary: RadiologySummaryResult | null,
  radiologyProgression: RadiologyProgressionResult | null,
  integratedRadiologyAnalysis: IntegratedClinicalAnalysisResult | null
}
```

---

## 데이터 흐름

### 1. 전체 분석 (summarize_patient)
```
클라이언트 데이터
    ↓
emit('summarize_patient', SummarizePatientRequest)
    ↓
의료 그래프 워크플로우
    ├─ 경과기록 → ProgressNoteResult
    ├─ 활력징후+간호 → VsNsSummaryResult
    ├─ 약물+진단 → PrescriptionSummaryResult
    ├─ 혈액검사 → LabSummaryResult
    ├─ 방사선(단일) → RadiologySummaryResult
    ├─ 방사선(진행) → RadiologyProgressionResult
    └─ 방사선(통합) → IntegratedClinicalAnalysisResult
    ↓
PatientSummaryResponse (모든 결과 포함)
    ↓
클라이언트에 emit_with_ack
```

### 2. 방사선만 분석 (query_radiology_analysis)
```
클라이언트 데이터
    ↓
emit('query_radiology_analysis', SummarizePatientRequest)
    ↓
의료 그래프 워크플로우
    ├─ [병렬 처리]
    └─ 방사선 관련 노드만 결과 수집
    ↓
RadiologyAnalysisResponse (3개 분석만)
    ↓
클라이언트에 emit_with_ack
```

---

## 파일 수정 사항

| 파일명 | 변경 내용 |
|--------|---------|
| `radiology_dto.py` | RadiologyReport 단순화 (findings만 유지) |
| `loading.py` | LoadingCompleteTarget에 방사선 타입 3개 추가 |
| `medical_graph.py` | 3개 분석 노드 추가 + State 필드 추가 + 워크플로우 통합 |
| `main.py` | 이전 이벤트 핸들러 제거, query_radiology_analysis 추가 |

---

## 사용 예제

### JavaScript/TypeScript 클라이언트

#### 예제 1: 전체 분석 요청
```typescript
const data = {
  patientInfo: {
    name: "김철수",
    chart: "2024-001",
    lastVisitYmd: "2024-11-27",
    hpTel: "010-1234-5678",
    sex: "M",
    age: "65"
  },
  nursingRecords: [/* 간호 기록 */],
  progressNotes: [/* 경과기록 */],
  vitalSigns: [/* 활력징후 */],
  medications: [/* 약물 */],
  diagnosisRecords: [/* 진단 */],
  labs: [/* 혈액검사 */],
  radiologyReports: [
    {
      ymd: "2024-11-27",
      time: "10:30",
      modality: "CT",
      examType: "흉부",
      findings: "우상엽에 경화 음영 관찰, 이전 검사 대비 크기 안정적"
    }
  ]
};

socket.emit('summarize_patient', data, (response) => {
  console.log('전체 분석 결과:', response);
  
  // 방사선 분석 결과 접근
  const radiologySummary = response.radiologySummary;
  const progression = response.radiologyProgression;
  const integrated = response.integratedRadiologyAnalysis;
});
```

#### 예제 2: 방사선만 분석
```typescript
socket.emit('query_radiology_analysis', data, (response) => {
  console.log('방사선 분석만:', response);
  
  if (response.radiologySummary) {
    console.log('주요 소견:', response.radiologySummary.mainFinding);
    console.log('긴급 소견:', response.radiologySummary.urgentFindings);
  }
  
  if (response.radiologyProgression) {
    console.log('진행 추세:', response.radiologyProgression.overallTrend);
  }
});
```

---

## 성능 특성

### 병렬 처리
- 모든 분석 노드 **동시 실행** (LangGraph의 병렬 처리)
- 순차 처리 오버헤드 제거

### 조건부 실행
- `radiologyReports` 없으면 방사선 노드 **스킵**
- `radiologyReports` 1개만 있으면 progression 노드 **스킵**
- 다른 임상 데이터 부재 시에도 자동 대응

### 최적화
- 최신 검사만 단일 분석 (이전 검사 자동 정렬)
- VsModels 재사용 (메모리 효율)
- 활력징후 최근 항목만 추출

---

## 주요 개선 사항

1. **통합 워크플로우**: 방사선을 다른 임상 데이터와 함께 분석
2. **단순화된 입력**: RadiologyReport를 최소 필드로 축소
3. **병렬 처리**: 모든 분석 동시 실행으로 응답 시간 단축
4. **유연한 쿼리**: 필요시 방사선만 추출 가능
5. **타입 안전성**: CamelModel + Pydantic 검증
6. **자동 에러 핸들링**: 노드 내 try-except + 그래프 상태 관리

---

## 향후 확장

1. 다중 모달리티 비교 (X-ray vs CT vs MRI)
2. AI 기반 이상 탐지 (이상 패턴 자동 식별)
3. 임상 가이드라인 통합 (진료 표준과 비교)
4. 동적 노드 추가 (사용자 정의 분석)
5. 배치 처리 (여러 환자 동시 분석)
6. 실시간 모니터링 대시보드
