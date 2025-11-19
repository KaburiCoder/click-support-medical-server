import pandas as pd

from typing import Iterable, Optional
from pydantic import BaseModel, Field
from src.sio.features.medical.dto import NursingRecord, VitalSign


class VsModel(BaseModel):
  date: Optional[str] = Field(default=None, description="측정일자 (YYYYMMDD)")
  high_pressure: Optional[str] = Field(default=None, description="수축기 혈압")
  low_pressure: Optional[str] = Field(default=None, description="이완기 혈압")
  pulse: Optional[str] = Field(default=None, description="심박수")
  weight: Optional[str] = Field(default=None, description="체중")
  temperature: Optional[str] = Field(default=None, description="체온")
  respiration: Optional[str] = Field(default=None, description="호흡수")
  spo2: Optional[str] = Field(default=None, description="산소포화도")

  def add_recently_from_vss(self, vs_list: Iterable[VitalSign]) -> None:
    for vs in vs_list:
      if self.__add_recently_from_vs(vs):
        break

  def add_from_vs(self, vs: VitalSign) -> None:
    if not self.date:
      self.date = vs['ymd']

    if self.high_pressure is None and vs['highPressure']:
      self.high_pressure = vs['highPressure']
    if self.low_pressure is None and vs['lowPressure']:
      self.low_pressure = vs['lowPressure']
    if self.pulse is None and vs['pulse']:
      self.pulse = vs['pulse']
    if self.weight is None and vs['weight']:
      self.weight = vs['weight']
    if self.temperature is None and vs['temperature']:
      self.temperature = vs['temperature']
    if self.respiration is None and vs['respiration']:
      self.respiration = vs['respiration']
    if self.spo2 is None and vs['spo2']:
      self.spo2 = vs['spo2']

  def __add_recently_from_vs(self, vs: VitalSign) -> bool:
    """
    vs(ORM 객체)에서 값이 비어있는 항목만 할당. 5개 모두 채워지면 True 반환.
    """
    self.add_from_vs(vs)

    # 5개 모두 값이 있으면 True
    return all([
        self.high_pressure,
        self.low_pressure,
        self.pulse,
        self.temperature,
        self.respiration
    ])


class VsModels(list[VsModel]):
  def add_recently_from_vss(self, vs_list: Iterable[VitalSign]) -> None:
    for vs in vs_list:
      vs_model = VsModel()
      vs_model.add_from_vs(vs)
      self.append(vs_model)

  def get_markdown_table(self):
    pd_vs = pd.DataFrame([vs_model.model_dump() for vs_model in self])
    pd_vs = pd_vs.rename(columns={
        "date": "측정일자",
        "high_pressure": "수축기 혈압",
        "low_pressure": "이완기 혈압",
        "pulse": "심박수",
        "temperature": "체온",
        "respiration": "호흡수"
    })
    return pd_vs.to_markdown(index=False)

  def get_jsonable(self) -> list[dict]:
    return [vs_model.model_dump() for vs_model in self]


class NsModel(BaseModel):
  date: str
  time: str
  nursing_diagnosis: str = Field(..., description="간호 문제")
  nursing_intervention: str = Field(..., description="간호 처치")


class NsModels(list[NsModel]):
  def add_from_nss(self, nss: list[NursingRecord]) -> None:
    for ns in nss:
      ns_model = NsModel(
          date=ns['ymd'],
          time=ns['time'],
          nursing_diagnosis=ns['nursingDiagnosis'] or "",
          nursing_intervention=ns['nursingIntervention'] or ""
      )
      self.append(ns_model)

  def get_markdown_table(self):
    import pandas as pd
    pd_ns = pd.DataFrame([ns_model.model_dump() for ns_model in self])
    pd_ns = pd_ns.rename(columns={
        "date": "작성일자",
        "time": "작성시간",
        "nursing_diagnosis": "간호 문제",
        "nursing_intervention": "간호 처치"
    })
    return pd_ns.to_markdown(index=False)
