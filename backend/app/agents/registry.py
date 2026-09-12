from backend.app.agents.cfo import CFOAgent
from backend.app.agents.cto import CTOAgent
from backend.app.agents.cmo import CMOAgent
from backend.app.agents.coo import COOAgent
from backend.app.agents.cpo import CPOAgent
from backend.app.agents.cro import CROAgent
from backend.app.agents.cso import CSOAgent
from backend.app.agents.chro import CHROAgent
from backend.app.agents.legal import LegalAgent
from backend.app.agents.risk import RiskAgent

# =====================================================
# FAST MODE AGENTS
# =====================================================

from backend.app.agents.fast_cfo import FastCFOAgent
from backend.app.agents.fast_cto import FastCTOAgent
from backend.app.agents.fast_cmo import FastCMOAgent
from backend.app.agents.fast_coo import FastCOOAgent
from backend.app.agents.fast_cpo import FastCPOAgent
from backend.app.agents.fast_cro import FastCROAgent
from backend.app.agents.fast_cso import FastCSOAgent
from backend.app.agents.fast_chro import FastCHROAgent
from backend.app.agents.fast_legal import FastLegalAgent
from backend.app.agents.fast_risk import FastRiskAgent


# =====================================================
# AVAILABLE AGENTS
# =====================================================

AVAILABLE_AGENTS = {
    "cfo": {
        "name": "CFO",
        "class": CFOAgent
    },
    "cto": {
        "name": "CTO",
        "class": CTOAgent
    },
    "cmo": {
        "name": "CMO",
        "class": CMOAgent
    },
    "coo": {
        "name": "COO",
        "class": COOAgent
    },
    "cpo": {
        "name": "CPO",
        "class": CPOAgent
    },
    "cro": {
        "name": "CRO",
        "class": CROAgent
    },
    "cso": {
        "name": "CSO",
        "class": CSOAgent
    },
    "chro": {
        "name": "CHRO",
        "class": CHROAgent
    },
    "legal": {
        "name": "Legal",
        "class": LegalAgent
    },
    "risk": {
        "name": "Risk",
        "class": RiskAgent
    }
}


# =====================================================
# FAST AGENTS
# =====================================================

FAST_AGENTS = {
    "cfo": FastCFOAgent,
    "cto": FastCTOAgent,
    "cmo": FastCMOAgent,
    "coo": FastCOOAgent,
    "cpo": FastCPOAgent,
    "cro": FastCROAgent,
    "cso": FastCSOAgent,
    "chro": FastCHROAgent,
    "legal": FastLegalAgent,
    "risk": FastRiskAgent
}


# =====================================================
# CREATE SELECTED AGENTS
# =====================================================

def create_selected_agents(
    selected_names,
    llm,
    execution_mode="accurate"
):
    """
    Create selected analyst agents.

    Accurate Mode:
        Uses the original agent classes.

    Fast Mode:
        Uses the separate Fast Mode agent classes.
    """

    agents = {}

    for name in selected_names:

        name = name.lower().strip()

        if name not in AVAILABLE_AGENTS:
            continue

        # -------------------------------------------------
        # FAST MODE
        # -------------------------------------------------

        if execution_mode == "fast":
            agent_class = FAST_AGENTS[name]

        # -------------------------------------------------
        # ACCURATE MODE
        # -------------------------------------------------

        else:
            agent_class = AVAILABLE_AGENTS[name]["class"]

        agents[name] = agent_class(llm)

    return agents


# =====================================================
# GET AVAILABLE AGENTS
# =====================================================

def get_available_agents():
    """
    Return all available analyst agents.
    """

    return {
        name: info["name"]
        for name, info in AVAILABLE_AGENTS.items()
    }