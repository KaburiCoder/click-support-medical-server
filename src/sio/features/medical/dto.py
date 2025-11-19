from typing import TypedDict

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


class SummarizePatientRequest(TypedDict):
  patientInfo: PatientInfo
  nursingRecords: list[NursingRecord]
  progressNotes: list[ProgressNote]
  vitalSigns: list[VitalSign]
