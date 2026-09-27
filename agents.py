from typing import TypedDict, List
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from ingest import ingest_pipeline

vector_store = ingest_pipeline()

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

api_key = os.getenv("GROQ_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError("api_key is missing, add your api_key")
if not tavily_api_key:
    raise ValueError("tavily_api_key is missing, add your tavily_api_key")

llm = ChatGroq(api_key=api_key, model="openai/gpt-oss-120b", temperature= 0.1)

class AgentState(TypedDict):
    #agent inputs
    patient_id: str
    pain_lvl: int
    symptomps: str
    medication_taken: bool
    weight: float
    missed_reason: str
    history: list[dict]
    # agent outputs
    trajectory: str
    deviation: bool
    risk_level: str
    recommendation: str
    




def stateanalyst_agent(state: AgentState):
    pain_lvl = state["pain_lvl"]
    symptomps = state["symptomps"]
    medication_taken = state["medication_taken"]
    weight = state["weight"]
    missed_reason = state["missed_reason"]
    history = state["history"]
    
    prompt =  f"""you are a pataint recovery analyst
                today's check-in:
                - pain_lvl: {pain_lvl}/10
                - symptomps: {symptomps}
                - medication_taken: {medication_taken}
                - weight: {weight}
                - reason if missed: {missed_reason}
                past check-ins:
                {history}
                
              analize the recovery trajectory. is patient improving, stable or declining ?
              describe the key changes over time in 3 - 4 sentences"""
    response = llm.invoke(prompt)
    return {"trajectory":response.content}

def deviation_detector_agent(state: AgentState):
    trajectory = state["trajectory"]
    docs = vector_store.similarity_search(trajectory, k=3)
    medical_guidlines = "/n".join([d.page_content for d in docs])
    prompt = f""""
            patient trajectory: {trajectory}
            medical guidlines: {medical_guidlines}
            
            based on the patient trajectory and the medical guidlines, 
            is the patient deviating? answer ONLY YES or NO"""
    response = llm.invoke(prompt)
    if "yes" in response.content.lower():
        deviation = True
    else:
        deviation = False
    return {"deviation": deviation}
def risk_trigger_agent(state: AgentState):
    deviation = state["deviation"]
    trajectory = state["trajectory"]
    prompt = f""""
            patient trajectory: {trajectory}
            deviation: {deviation}
            
            based on the patient trajectory and the deviation, 
            what is the risk level of the patient?
            Respond only in this format: RISK: <Low/Medium/High>
            RECOMMENDATION: <2-3 lines advice for the patient>"""
    response = llm.invoke(prompt)
    parts = response.content.split("RECOMMENDATION:")
    recommendation = parts[1].strip() if len(parts) > 1 else ""
    return {"risk_level": response.content.split("RISK:")[1].split("RECOMMENDATION:")[0].strip(),"recommendation": recommendation}

def router_agent(state: AgentState):
    deviation = state["deviation"]
    if deviation == True:
        return "risk_trigger_agent"
    else:
        return END
    
graph = StateGraph(AgentState)

graph.add_node("stateanalyst_agent", stateanalyst_agent)
graph.add_node("deviation_detector_agent", deviation_detector_agent)
graph.add_node("risk_trigger_agent", risk_trigger_agent)
graph.add_edge(START, "stateanalyst_agent")
graph.add_edge("stateanalyst_agent", "deviation_detector_agent")
graph.add_conditional_edges("deviation_detector_agent", router_agent)
graph.add_edge("risk_trigger_agent", END)

agent = graph.compile()





    


        






