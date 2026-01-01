"""
Developer Category → Consumer Capability mapping (WebManus).

The source dataset (`data/agents.json`) is developer-facing and tends to use
implementation terms (e.g. "rag", "langchain"). WebManus needs consumer-facing
capability tags that describe outcomes/use-cases.
"""

from __future__ import annotations

from typing import Dict, List


CATEGORY_TO_CAPABILITIES: Dict[str, List[str]] = {
    # Original category (developer) -> consumer capabilities
    "rag": ["document-analysis", "knowledge-base", "qa"],
    "chatbot": ["conversation", "customer-support"],
    "agent": ["automation", "task-execution"],
    "multi_agent": ["complex-workflow", "team-coordination"],
    "automation": ["automation", "workflow", "scheduling"],
    "search": ["research", "information-retrieval"],
    "vision": ["image-analysis", "visual-recognition"],
    "voice": ["speech-to-text", "text-to-speech", "audio"],
    "coding": ["code-generation", "debugging", "development"],
    "finance": ["financial-analysis", "trading", "accounting"],
    "research": ["research", "data-analysis", "report-writing"],
    "other": ["general-purpose"],
}


FRAMEWORK_HINTS: Dict[str, List[str]] = {
    # Framework -> capabilities (best-effort, used as hints)
    "langchain": ["document-analysis", "automation"],
    "crewai": ["team-coordination", "complex-workflow"],
    "autogen": ["team-coordination", "complex-workflow", "automation"],
    "llamaindex": ["document-analysis", "knowledge-base"],
}


CAPABILITY_LABELS: Dict[str, str] = {
    "document-analysis": "📄 Document Analysis",
    "knowledge-base": "🧠 Knowledge Base",
    "qa": "❓ Q&A",
    "conversation": "💬 Conversation",
    "customer-support": "🎧 Customer Support",
    "automation": "⚡ Automation",
    "task-execution": "✅ Task Execution",
    "workflow": "🧩 Workflow",
    "scheduling": "🗓️ Scheduling",
    "complex-workflow": "🧠 Complex Workflow",
    "team-coordination": "👥 Team Coordination",
    "research": "🔍 Research",
    "information-retrieval": "🧭 Information Retrieval",
    "code-generation": "💻 Code Generation",
    "debugging": "🪲 Debugging",
    "development": "🧑‍💻 Development",
    "financial-analysis": "📊 Financial Analysis",
    "trading": "📈 Trading",
    "accounting": "🧾 Accounting",
    "image-analysis": "🖼️ Image Analysis",
    "visual-recognition": "👁️ Visual Recognition",
    "speech-to-text": "🎤 Speech to Text",
    "text-to-speech": "🔊 Text to Speech",
    "audio": "🎧 Audio",
    "data-analysis": "📎 Data Analysis",
    "report-writing": "📝 Report Writing",
    "general-purpose": "✨ General Purpose",
}


def infer_capabilities(agent: dict) -> List[str]:
    """Infer consumer capabilities from a developer-facing agent record."""
    caps = set()

    category = (agent.get("category") or "other").lower()
    caps.update(CATEGORY_TO_CAPABILITIES.get(category, ["general-purpose"]))

    for fw in (agent.get("frameworks") or []):
        fw_l = str(fw).lower().strip()
        if fw_l in FRAMEWORK_HINTS:
            caps.update(FRAMEWORK_HINTS[fw_l])

    # Fallback: if everything failed, still keep a single stable tag
    if not caps:
        caps.add("general-purpose")

    return sorted(caps)

