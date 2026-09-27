from fastapi import FastAPI
from pydantic import BaseModel
from agents import agent
from database import save_checkin, fetch_history


app = FastAPI()


class PatientData(BaseModel):
    patient_id: str
    pain_lvl: int
    symptomps: str
    medication_taken: bool
    weight: float
    missed_reason: str


class CheckInResponse(BaseModel):
    trajectory: str
    deviation: bool
    risk_level: str | None = None
    recommendation: str | None = None
    

@app.post("/check_in", response_model=CheckInResponse)
async def check_in(data: PatientData) -> CheckInResponse:
    save_checkin(data.patient_id, data.pain_lvl, data.symptomps, data.medication_taken, data.weight, data.missed_reason)
    history = fetch_history(data.patient_id)
    state = data.model_dump()
    state["history"] = history
    result = await agent.ainvoke(state)
    return CheckInResponse(**result)

    