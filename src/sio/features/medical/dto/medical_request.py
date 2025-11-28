from typing import TypedDict
from src.sio.features.medical.dto.radiology_dto import RadiologyReport

class PatientInfo(TypedDict):
  name: str
  chart: str
  lastVisitYmd: str
  hpTel: str
  sex: str
  age: str

class NursingRecord(TypedDict):
  ymd: str
  time: str
  nursingDiagnosis: str       # 간호 문제
  nursingIntervention: str    # 간호 처치


class ProgressNote(TypedDict):
  ymd: str
  time: str
  progress: str


class VitalSign(TypedDict):
  ymd: str
  time: str
  highPressure: str    # 수축기 혈압
  lowPressure: str     # 이완기 혈압
  pulse: str           # 심박수
  weight: str          # 체중
  temperature: str     # 체온
  respiration: str     # 호흡수
  spo2: str            # 산소포화도


class DiagnosisDetail(TypedDict):
  icdCode: str
  diagnosisName: str


class DiagnosisRecord(TypedDict):
  ymd: str
  diagnoses: list[DiagnosisDetail]


class Medication(TypedDict):
  sYmd: str                    # 투약 시작일
  eYmd: str                    # 투약 종료일
  medicationYmds: list[str]    # 투약 세부 일자
  medicationName: str          # 약품명
  route: str                   # 투여 경로
  dose: float                  # 1회 투약량
  frequency: int               # 횟수
  totalDays: int               # 총투여일수
  administration: str          # 용법
  note: str                    # 참고사항

class Lab(TypedDict):
  ymd: str
  testName: str
  subTestName: str
  resultValue: str
  unit: str
  normalRange: str
  note: str

class SummarizePatientRequest(TypedDict):
  patientInfo: PatientInfo
  nursingRecords: list[NursingRecord]
  progressNotes: list[ProgressNote]
  vitalSigns: list[VitalSign]
  medications: list[Medication]
  diagnosisRecords: list[DiagnosisRecord]
  labs: list[Lab]
  radiologyReports: list[RadiologyReport]