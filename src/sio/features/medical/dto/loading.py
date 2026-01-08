from typing import Literal

from src.common import CamelModel


type LoadingStatus = Literal["processing", "done"]
type LoadingCompleteTarget = Literal[
    "progress_notes", "ns_vs",
    "prescriptions", "labs",
  "radiology", "surgery", "clinical_summary"]


class Loading(CamelModel):
  status: LoadingStatus = "processing"
  complete_target: LoadingCompleteTarget | None = None

  def to_json(self):
    return self.model_dump(by_alias=True)
