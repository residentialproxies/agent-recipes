"""
Data-related functions and pSEO page configurations.
Includes related agent finding and all page configuration data.
"""

from __future__ import annotations

from typing import Callable


def _find_related_agents(agent: dict, all_agents: list[dict], limit: int = 4) -> list[dict]:
    """
    Find related agents based on category, frameworks, and providers.
    Uses Jaccard similarity for ranking.
    """
    agent_id = agent.get("id", "")
    agent_cat = agent.get("category", "")
    agent_frameworks = set(agent.get("frameworks", []))
    agent_providers = set(agent.get("llm_providers", []))

    scores = []
    for other in all_agents:
        try:
            if other.get("id") == agent_id:
                continue

            score = 0

            # Category match (highest weight)
            if other.get("category") == agent_cat:
                score += 3

            # Framework overlap (Jaccard)
            other_frameworks = set(other.get("frameworks", []))
            if agent_frameworks and other_frameworks:
                intersection = len(agent_frameworks & other_frameworks)
                union = len(agent_frameworks | other_frameworks)
                score += 2 * (intersection / union) if union > 0 else 0

            # Provider overlap (Jaccard)
            other_providers = set(other.get("llm_providers", []))
            if agent_providers and other_providers:
                intersection = len(agent_providers & other_providers)
                union = len(agent_providers | other_providers)
                score += 1 * (intersection / union) if union > 0 else 0

            if score > 0:
                scores.append((score, other))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue

    # Sort by score descending and return top matches
    scores.sort(key=lambda x: -x[0])
    return [agent for _, agent in scores[:limit]]


# pSEO Category landing page configurations
CATEGORY_PAGES = [
    (
        "rag-tutorials",
        "RAG Tutorials",
        lambda a: a.get("category") == "rag",
        "RAG Tutorials & Examples",
        "Build Retrieval Augmented Generation systems with vector databases, document loaders, and LLM query engines.",
    ),
    (
        "openai-agents",
        "OpenAI Agents",
        lambda a: "openai" in a.get("llm_providers", []),
        "OpenAI Agents & GPT Examples",
        "LLM agents powered by OpenAI GPT-4, GPT-3.5, Assistants API, function calling, and more.",
    ),
    (
        "multi-agent-systems",
        "Multi-Agent Systems",
        lambda a: a.get("category") == "multi_agent",
        "Multi-Agent Systems & Orchestration",
        "Multi-agent architectures with CrewAI, LangChain agents, and custom orchestrators for complex task automation.",
    ),
    (
        "local-llm-agents",
        "Local LLM Agents",
        lambda a: a.get("supports_local_models", False) or "ollama" in a.get("llm_providers", []) or "local" in a.get("llm_providers", []),
        "Local LLM Agents & Privacy-First Examples",
        "Run LLM agents locally with Ollama, Llama, Mistral, and other open-source models for privacy and cost savings.",
    ),
]


# Framework-specific page configurations
FRAMEWORK_PAGES = [
    (
        "langchain-agents",
        "LangChain Agents",
        lambda a: "langchain" in a.get("frameworks", []),
        "LangChain Agents & Examples",
        "Build AI agents using LangChain framework. Includes agents, chains, tools, and RAG implementations with LangChain.",
        """<section class="about">
<h2>Why Use LangChain?</h2>
<p>LangChain is the most popular framework for building LLM applications. It provides abstractions for agents, chains, tools, memory, and RAG pipelines. With LangChain, you can quickly prototype and productionize AI agents.</p>
<h2>Getting Started with LangChain</h2>
<p>Install with <code>pip install langchain</code>. Browse examples below to see different agent patterns like ReAct agents, OpenAI functions, custom tools, and multi-agent collaboration.</p>
</section>""",
    ),
    (
        "crewai-agents",
        "CrewAI Agents",
        lambda a: "crewai" in a.get("frameworks", []),
        "CrewAI Multi-Agent Examples",
        "Build multi-agent systems using CrewAI framework. Role-based agents with delegation and collaboration patterns.",
        """<section class="about">
<h2>Why Use CrewAI?</h2>
<p>CrewAI specializes in multi-agent systems where each agent has a specific role. Agents can delegate tasks to each other, collaborate on complex problems, and use tools autonomously. Perfect for automation workflows.</p>
<h2>CrewAI Concepts</h2>
<p>Agents have roles, goals, and backstories. They can use tools and delegate to other agents. Browse examples to see practical implementations.</p>
</section>""",
    ),
    (
        "phidata-agents",
        "PhiData Agents",
        lambda a: "phidata" in a.get("frameworks", []),
        "PhiData Agent Examples",
        "Build production-ready agents with PhiData framework. Includes monitoring, evaluation, and deployment tools.",
        """<section class="about">
<h2>Why Use PhiData?</h2>
<p>PhiData focuses on production-ready agents with built-in monitoring, evaluation, and deployment capabilities. It's designed for teams building serious AI applications.</p>
</section>""",
    ),
    (
        "raw-api-agents",
        "Raw API Agents",
        lambda a: "raw_api" in a.get("frameworks", []),
        "Direct API Agent Examples",
        "Build AI agents using direct API calls to OpenAI, Anthropic, Google, and other providers without framework overhead.",
        """<section class="about">
<h2>Why Use Raw APIs?</h2>
<p>Direct API calls give you maximum control and zero dependencies. Great for learning how LLM APIs work, building lightweight agents, or when you don't need framework features.</p>
<h2>Getting Started</h2>
<p>All you need is an API key. Examples show chat completion, function calling, streaming, and more using official SDKs.</p>
</section>""",
    ),
]


# Provider-specific page configurations
PROVIDER_PAGES = [
    (
        "anthropic-agents",
        "Anthropic Claude Agents",
        lambda a: "anthropic" in a.get("llm_providers", []),
        "Anthropic Claude Agents & Examples",
        "Build AI agents using Anthropic's Claude API. Includes Claude 3.5 Haiku, Sonnet, and Opus examples with function calling.",
        """<section class="about">
<h2>Why Use Anthropic Claude?</h2>
<p>Claude is known for strong reasoning, long context windows (200K tokens), and careful outputs. Great for complex tasks requiring analysis or generation of long content.</p>
<h2>Getting Started</h2>
<p>Get an API key from console.anthropic.com. Install with <code>pip install anthropic</code>.</p>
</section>""",
    ),
    (
        "google-agents",
        "Google Gemini Agents",
        lambda a: "google" in a.get("llm_providers", []),
        "Google Gemini Agents & Examples",
        "Build AI agents using Google's Gemini API. Includes Gemini Pro, Flash, and specialized models.",
        """<section class="about">
<h2>Why Use Google Gemini?</h2>
<p>Gemini offers strong multimodal capabilities, competitive pricing, and Google's infrastructure. Excellent for vision tasks and Google Workspace integration.</p>
<h2>Getting Started</h2>
<p>Get an API key from AI Studio. Install with <code>pip install google-generativeai</code>.</p>
</section>""",
    ),
    (
        "cohere-agents",
        "Cohere Agents",
        lambda a: "cohere" in a.get("llm_providers", []),
        "Cohere Command & Embed Agents",
        "Build AI agents using Cohere's Command and Embed models. Strong for RAG and enterprise use cases.",
        """<section class="about">
<h2>Why Use Cohere?</h2>
<p>Cohere focuses on enterprise use cases with strong embedding models and RAG capabilities. Their API is designed for production applications.</p>
</section>""",
    ),
    (
        "huggingface-agents",
        "HuggingFace Agents",
        lambda a: "huggingface" in a.get("llm_providers", []),
        "HuggingFace Inference API Agents",
        "Build agents using HuggingFace's inference API and open-source models.",
        """<section class="about">
<h2>Why Use HuggingFace?</h2>
<p>Access thousands of open-source models through one API. Great for specialized models, cost optimization, and privacy requirements.</p>
</section>""",
    ),
]


# Complexity-based page configurations
COMPLEXITY_PAGES = [
    (
        "beginner-projects",
        "Beginner Projects",
        lambda a: a.get("complexity") == "beginner",
        "Beginner AI Agent Projects",
        "Start your AI agent journey with beginner-friendly projects. Perfect for learning LLM agent fundamentals.",
        "Beginner",
    ),
    (
        "intermediate-projects",
        "Intermediate Projects",
        lambda a: a.get("complexity") == "intermediate",
        "Intermediate AI Agent Projects",
        "Expand your skills with intermediate agent projects. RAG, tool use, and multi-agent patterns.",
        "Intermediate",
    ),
    (
        "advanced-projects",
        "Advanced Projects",
        lambda a: a.get("complexity") == "advanced",
        "Advanced AI Agent Projects",
        "Master advanced agent architectures. Complex multi-agent systems, production deployments, and cutting-edge patterns.",
        "Advanced",
    ),
]


# Comparison page configurations
COMPARISON_CONFIGS = [
    {
        "key": "langchain-vs-llamaindex",
        "title": "LangChain vs LlamaIndex",
        "description": "Compare LangChain and LlamaIndex for building AI agents. Learn about their strengths, use cases, and code examples.",
        "left": "LangChain",
        "right": "LlamaIndex",
        "left_filter": lambda a: "langchain" in a.get("frameworks", []),
        "right_filter": lambda a: "llamaindex" in a.get("frameworks", []),
        "content": """<section class="about">
<h2>LangChain Overview</h2>
<p>LangChain is a general-purpose framework for building LLM applications. It excels at agent orchestration, chain composition, and tool use. Ideal for complex multi-step reasoning and agent workflows.</p>
<h2>LlamaIndex Overview</h2>
<p>LlamaIndex (formerly GPT Index) specializes in RAG and data indexing. It provides excellent connectors to data sources and advanced retrieval strategies. Best for knowledge-intensive applications.</p>
<h2>When to Choose</h2>
<p>Choose LangChain for general agent development and complex workflows. Choose LlamaIndex when your primary need is RAG and connecting LLMs to your data. Many projects use both together.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Can I use LangChain and LlamaIndex together?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes! They work well together. Use LlamaIndex for data ingestion and retrieval, then pass results to LangChain agents for reasoning and action.",
                },
            },
            {
                "@type": "Question",
                "name": "Which has better performance?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Both are actively optimized. LangChain has more abstraction overhead while LlamaIndex is lighter for pure RAG. Choose based on your use case, not perceived performance.",
                },
            },
        ],
    },
    {
        "key": "crewai-vs-autogen",
        "title": "CrewAI vs AutoGen",
        "description": "Compare CrewAI and AutoGen for multi-agent systems. Understand their approaches to agent collaboration and orchestration.",
        "left": "CrewAI",
        "right": "AutoGen",
        "left_filter": lambda a: "crewai" in a.get("frameworks", []),
        "right_filter": lambda a: "autogen" in a.get("frameworks", []),
        "content": """<section class="about">
<h2>CrewAI Overview</h2>
<p>CrewAI focuses on role-based multi-agent systems. Define agents with specific roles, goals, and backstories. Agents can delegate tasks and collaborate naturally. Great for business process automation.</p>
<h2>AutoGen Overview</h2>
<p>Microsoft's AutoGen enables multi-agent conversations through a simple interface. Agents communicate to solve tasks, with human-in-the-loop options. Excellent for research and complex problem-solving.</p>
<h2>Key Differences</h2>
<p>CrewAI emphasizes production-ready role definition. AutoGen focuses on conversational dynamics. Both support tool use and delegation, but with different mental models.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Which is easier for beginners?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "CrewAI's role-based approach is more intuitive for many. AutoGen's conversation model is powerful but may require more experimentation to master.",
                },
            },
        ],
    },
    {
        "key": "openai-vs-anthropic",
        "title": "OpenAI vs Anthropic",
        "description": "Compare OpenAI GPT and Anthropic Claude for AI agents. Pricing, capabilities, and best use cases.",
        "left": "OpenAI",
        "right": "Anthropic",
        "left_filter": lambda a: "openai" in a.get("llm_providers", []),
        "right_filter": lambda a: "anthropic" in a.get("llm_providers", []),
        "content": """<section class="about">
<h2>OpenAI GPT Overview</h2>
<p>OpenAI offers GPT-4, GPT-4o, and GPT-3.5 with excellent function calling, vision capabilities, and the Assistants API. Largest ecosystem and tool support.</p>
<h2>Anthropic Claude Overview</h2>
<p>Claude 3.5 Haiku, Sonnet, and Opus offer strong reasoning, 200K context windows, and careful outputs. Known for reduced hallucination and excellent for analysis tasks.</p>
<h2>Pricing Comparison</h2>
<p>OpenAI GPT-3.5 is most cost-effective for simple tasks. Claude 3.5 Haiku offers great value. GPT-4o and Claude Opus are premium for complex reasoning.</p>
<h2>Decision Factors</h2>
<p>Choose OpenAI for ecosystem, vision, and Assistants API. Choose Claude for long context, careful outputs, and complex reasoning tasks.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Which has better function calling?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Both have excellent function calling. OpenAI's implementation is more mature with broader tool support. Claude 3.5 has competitive function calling with often better reliability.",
                },
            },
            {
                "@type": "Question",
                "name": "How do context windows compare?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Claude offers 200K tokens context. GPT-4 Turbo offers 128K tokens. Both support large document analysis. Claude's larger window can be advantageous for extensive document processing.",
                },
            },
        ],
    },
    {
        "key": "langchain-vs-raw-api",
        "title": "LangChain vs Raw API",
        "description": "Compare using LangChain framework vs direct API calls for AI agents. When to use each approach.",
        "left": "LangChain",
        "right": "Raw API",
        "left_filter": lambda a: "langchain" in a.get("frameworks", []),
        "right_filter": lambda a: "raw_api" in a.get("frameworks", []),
        "content": """<section class="about">
<h2>LangChain Framework Approach</h2>
<p>LangChain provides abstractions for agents, chains, tools, memory, and RAG. Great for rapid development, standardizing patterns, and leveraging community components. Adds dependency overhead.</p>
<h2>Raw API Approach</h2>
<p>Direct API calls to OpenAI, Anthropic, or Google give maximum control with zero dependencies. Best for simple agents, learning, and when framework features aren't needed.</p>
<h2>When to Use Each</h2>
<p>Use raw APIs for simple chatbots, one-off tasks, and learning fundamentals. Use LangChain for complex workflows, RAG systems, multi-agent setups, and when you need built-in integrations.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Is LangChain too heavy for simple projects?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "For very simple projects, raw APIs may be sufficient. But LangChain's value becomes clear as complexity grows. Start with raw APIs to learn, then adopt LangChain as needs evolve.",
                },
            },
        ],
    },
    {
        "key": "google-vs-openai",
        "title": "Google vs OpenAI",
        "description": "Compare Google Gemini and OpenAI GPT models. Features, pricing, and capabilities comparison.",
        "left": "Google Gemini",
        "right": "OpenAI",
        "left_filter": lambda a: "google" in a.get("llm_providers", []),
        "right_filter": lambda a: "openai" in a.get("llm_providers", []),
        "content": """<section class="about">
<h2>Google Gemini Overview</h2>
<p>Gemini Pro and Flash models offer strong multimodal capabilities, competitive pricing, and Google Cloud integration. Excellent for vision tasks and Google Workspace users.</p>
<h2>OpenAI GPT Overview</h2>
<p>GPT-4, GPT-4o, and GPT-3.5 lead in capabilities and ecosystem. Best-in-class function calling, Assistants API, and broadest tool support.</p>
<h2>Decision Factors</h2>
<p>Choose Google for cost-sensitive projects, vision-heavy applications, or Google Cloud integration. Choose OpenAI for cutting-edge capabilities, ecosystem, and when you need the best performance.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Which is more cost-effective?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Gemini Flash is very cost-effective for high-volume tasks. GPT-3.5 is also very affordable. Compare latest pricing as it changes frequently - both offer competitive tiers.",
                },
            },
        ],
    },
    {
        "key": "local-vs-cloud-llms",
        "title": "Local vs Cloud LLMs",
        "description": "Compare running LLMs locally vs using cloud APIs. Privacy, cost, and performance considerations.",
        "left": "Local LLMs",
        "right": "Cloud LLMs",
        "left_filter": lambda a: a.get("supports_local_models", False) or "ollama" in a.get("llm_providers", []) or "local" in a.get("llm_providers", []),
        "right_filter": lambda a: any(p in ["openai", "anthropic", "google", "cohere"] for p in a.get("llm_providers", [])),
        "content": """<section class="about">
<h2>Local LLMs (Ollama, Llama, Mistral)</h2>
<p>Run models on your hardware for complete privacy, no API costs, and offline capability. Requires GPU for good performance. Models like Llama 3, Mistral, and Phi-3 are surprisingly capable.</p>
<h2>Cloud LLMs (OpenAI, Anthropic, Google)</h2>
<p>Best-in-class models, instant scaling, zero infrastructure. Pay per usage with predictable costs. GPT-4 and Claude Opus still outperform most open models.</p>
<h2>Decision Framework</h2>
<p>Use local for: sensitive data, cost control, offline needs, and privacy requirements. Use cloud for: best quality, speed of development, and when model quality matters more than cost.</p>
<h2>Hybrid Approach</h2>
<p>Many production systems use both: local models for simple tasks and sensitive data, cloud models for complex reasoning. This optimizes both cost and quality.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What hardware do I need for local LLMs?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "For 7B models: 8GB GPU VRAM is comfortable. For 13B+: 16GB+ recommended. CPU-only is possible but slow. Quantized models (4-bit) reduce requirements significantly. Ollama makes setup easy.",
                },
            },
            {
                "@type": "Question",
                "name": "Are local models good enough for production?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "It depends on your use case. Llama 3 8B and Mistral 7B are excellent for many tasks. For complex reasoning, GPT-4/Claude Opus still lead. Hybrid architectures often work best.",
                },
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Additional pSEO page configs (P2)
# ---------------------------------------------------------------------------

def _text_blob(agent: dict) -> str:
    parts = [
        agent.get("id") or "",
        agent.get("name") or "",
        agent.get("description") or "",
        agent.get("category") or "",
        agent.get("design_pattern") or "",
        " ".join(agent.get("frameworks") or []),
        " ".join(agent.get("llm_providers") or []),
        " ".join(agent.get("languages") or []),
    ]
    return " ".join([str(p) for p in parts if p]).lower()


def _has_any_keyword(agent: dict, keywords: list[str]) -> bool:
    if not keywords:
        return False
    blob = _text_blob(agent)
    return any((k or "").lower() in blob for k in keywords)


def _has_all_keywords(agent: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = _text_blob(agent)
    return all((k or "").lower() in blob for k in keywords)


DESIGN_PATTERNS: dict[str, dict] = {
    "rag-patterns": {
        "title": "RAG Pattern Agents",
        "description": "Retrieval-Augmented Generation implementation examples and patterns.",
        "keywords": ["rag", "retrieval", "vector", "embeddings"],
        "criteria": lambda a: (a.get("design_pattern") in {"rag", "rag_patterns"}) or (a.get("category") == "rag"),
    },
    "react-agents": {
        "title": "ReAct Agents",
        "description": "Reason + Act agent examples that use tools to solve tasks step-by-step.",
        "keywords": ["react", "tool", "reasoning", "agent"],
        "criteria": lambda a: _has_any_keyword(a, ["react", "reason and act", "tool use"]),
    },
    "tool-use-agents": {
        "title": "Tool-Use Agents",
        "description": "Function calling and tool-using agents (APIs, search, retrieval, workflows).",
        "keywords": ["tool", "function calling", "tools", "actions"],
        "criteria": lambda a: _has_any_keyword(a, ["tool", "function", "function calling"]),
    },
    "plan-and-execute": {
        "title": "Plan-and-Execute Agents",
        "description": "Agents that plan first, then execute steps (often multi-agent or tool-based).",
        "keywords": ["plan", "execute", "planner", "steps"],
        "criteria": lambda a: _has_any_keyword(a, ["plan", "planner", "plan-and-execute", "plan and execute"]),
    },
    "reflection-agents": {
        "title": "Reflection Agents",
        "description": "Self-reflection / critique loops to improve outputs and reduce errors.",
        "keywords": ["reflection", "self critique", "critique", "reviser"],
        "criteria": lambda a: _has_any_keyword(a, ["reflection", "self-critique", "critique", "revise"]),
    },
}


BEST_OF_PAGES: dict[str, dict] = {
    "best-rag-agents-2025": {
        "title": "Best RAG Agents 2025",
        "description": "Top RAG implementation examples for building knowledge-aware AI applications.",
        "criteria": lambda a: a.get("category") == "rag",
        "sort_by": "stars",
    },
    "best-local-llm-agents": {
        "title": "Best Local LLM Agents",
        "description": "Strong examples that run on local models for privacy and cost savings.",
        "criteria": lambda a: bool(a.get("supports_local_models")) or _has_any_keyword(a, ["ollama", "local llm", "llama"]),
        "sort_by": "stars",
    },
    "best-multi-agent-systems": {
        "title": "Best Multi-Agent Systems",
        "description": "Top multi-agent orchestration examples and patterns.",
        "criteria": lambda a: a.get("category") == "multi_agent",
        "sort_by": "stars",
    },
    "best-openai-agents-for-beginners": {
        "title": "Best OpenAI Agents for Beginners",
        "description": "Beginner-friendly OpenAI agent examples with clear setup steps.",
        "criteria": lambda a: ("openai" in (a.get("llm_providers") or [])) and (a.get("complexity") == "beginner"),
        "sort_by": "stars",
    },
    "best-free-ai-agents": {
        "title": "Best Free AI Agents",
        "description": "Examples that prioritize open-source or local-first approaches.",
        "criteria": lambda a: bool(a.get("supports_local_models")) or ("huggingface" in (a.get("llm_providers") or [])),
        "sort_by": "stars",
    },
    "best-langchain-agents": {
        "title": "Best LangChain Agents",
        "description": "High-quality LangChain agent and RAG examples.",
        "criteria": lambda a: "langchain" in (a.get("frameworks") or []),
        "sort_by": "stars",
    },
    "best-crewai-agents": {
        "title": "Best CrewAI Agents",
        "description": "Best multi-agent examples built with CrewAI.",
        "criteria": lambda a: "crewai" in (a.get("frameworks") or []),
        "sort_by": "stars",
    },
    "best-automation-agents": {
        "title": "Best Automation Agents",
        "description": "Agent examples focused on workflow automation and integrations.",
        "criteria": lambda a: (a.get("category") == "automation") or _has_any_keyword(a, ["automation", "workflow", "zapier"]),
        "sort_by": "stars",
    },
    "best-coding-assistants": {
        "title": "Best Coding Assistants",
        "description": "Coding agents: code generation, refactors, review, and dev workflows.",
        "criteria": lambda a: (a.get("category") == "coding") or _has_any_keyword(a, ["code", "coding", "refactor", "developer"]),
        "sort_by": "stars",
    },
    "best-research-assistants": {
        "title": "Best Research Assistants",
        "description": "Research agents: browsing, summarization, and knowledge work.",
        "criteria": lambda a: (a.get("category") == "research") or _has_any_keyword(a, ["research", "paper", "literature"]),
        "sort_by": "stars",
    },
}


USE_CASES: dict[str, dict] = {
    "customer-support-agents": {
        "title": "Customer Support AI Agents",
        "description": "Build intelligent customer service chatbots with these agent examples.",
        "criteria": lambda a: _has_any_keyword(a, ["customer support", "support", "helpdesk", "ticket", "zendesk"]),
        "keywords": ["customer support", "helpdesk", "chatbot"],
    },
    "research-assistants": {
        "title": "Research Assistants",
        "description": "Research agents for search, summarization, and knowledge synthesis.",
        "criteria": lambda a: (a.get("category") == "research") or _has_any_keyword(a, ["research", "paper", "arxiv", "literature"]),
        "keywords": ["research", "papers", "summarize"],
    },
    "coding-assistants": {
        "title": "Coding Assistants",
        "description": "Coding agents for development workflows: generation, refactors, and review.",
        "criteria": lambda a: (a.get("category") == "coding") or _has_any_keyword(a, ["code", "coding", "refactor", "review"]),
        "keywords": ["coding", "refactor", "review"],
    },
    "content-generation": {
        "title": "Content Generation Agents",
        "description": "Content generation examples for writing, marketing, and documentation.",
        "criteria": lambda a: _has_any_keyword(a, ["content", "blog", "marketing", "copywriting", "generate"]),
        "keywords": ["content", "marketing", "writing"],
    },
    "data-analysis": {
        "title": "Data Analysis Agents",
        "description": "Data analysis agents for insights, SQL, charts, and automation.",
        "criteria": lambda a: _has_any_keyword(a, ["data analysis", "sql", "data", "analytics", "dashboard"]),
        "keywords": ["data", "sql", "analytics"],
    },
    "workflow-automation": {
        "title": "Workflow Automation Agents",
        "description": "Workflow automation agents that connect tools and execute tasks end-to-end.",
        "criteria": lambda a: (a.get("category") == "automation") or _has_any_keyword(a, ["workflow", "automation", "integrations"]),
        "keywords": ["workflow", "automation", "integrations"],
    },
}


TECH_COMBOS: dict[str, dict] = {
    "langchain-with-openai": {
        "title": "LangChain with OpenAI",
        "description": "Examples combining LangChain with OpenAI models and APIs.",
        "criteria": lambda a: ("langchain" in (a.get("frameworks") or [])) and ("openai" in (a.get("llm_providers") or [])),
        "keywords": ["langchain", "openai"],
    },
    "langchain-with-anthropic": {
        "title": "LangChain with Anthropic",
        "description": "LangChain examples using Anthropic Claude models.",
        "criteria": lambda a: ("langchain" in (a.get("frameworks") or [])) and ("anthropic" in (a.get("llm_providers") or [])),
        "keywords": ["langchain", "anthropic", "claude"],
    },
    "crewai-with-local-llms": {
        "title": "CrewAI with Local LLMs",
        "description": "CrewAI multi-agent examples that run on local models.",
        "criteria": lambda a: ("crewai" in (a.get("frameworks") or [])) and (bool(a.get("supports_local_models")) or _has_any_keyword(a, ["ollama", "local"])),
        "keywords": ["crewai", "local llm", "ollama"],
    },
    "rag-with-pinecone": {
        "title": "RAG with Pinecone",
        "description": "RAG examples using Pinecone as the vector database.",
        "criteria": lambda a: (a.get("category") == "rag") and _has_any_keyword(a, ["pinecone"]),
        "keywords": ["rag", "pinecone"],
    },
    "rag-with-chroma": {
        "title": "RAG with Chroma",
        "description": "RAG examples using Chroma/ChromaDB.",
        "criteria": lambda a: (a.get("category") == "rag") and _has_any_keyword(a, ["chroma", "chromadb"]),
        "keywords": ["rag", "chroma"],
    },
    "multi-agent-with-autogen": {
        "title": "Multi-Agent with AutoGen",
        "description": "Multi-agent orchestration examples using AutoGen.",
        "criteria": lambda a: _has_any_keyword(a, ["autogen"]) and ((a.get("category") == "multi_agent") or ("autogen" in (a.get("frameworks") or []))),
        "keywords": ["autogen", "multi-agent"],
    },
    "function-calling-with-gpt4": {
        "title": "Function Calling with GPT-4",
        "description": "Examples demonstrating function calling / tool use with GPT-4-style models.",
        "criteria": lambda a: _has_any_keyword(a, ["function calling", "tool", "tools", "gpt-4", "gpt4"]),
        "keywords": ["function calling", "gpt-4", "tools"],
    },
    "voice-agents-with-whisper": {
        "title": "Voice Agents with Whisper",
        "description": "Voice agent examples using speech-to-text (Whisper) and audio pipelines.",
        "criteria": lambda a: _has_any_keyword(a, ["whisper", "speech", "voice", "audio"]),
        "keywords": ["whisper", "voice", "speech"],
    },
}


# Tutorial/How-To page configurations
TUTORIAL_CONFIGS = [
    {
        "key": "build-rag-chatbot",
        "title": "How to Build a RAG Chatbot",
        "description": "Learn how to build a Retrieval Augmented Generation (RAG) chatbot from scratch. Complete guide with vector databases, document processing, and LLM integration.",
        "filter": lambda a: a.get("category") == "rag" or ("rag" in a.get("tags", [])),
        "difficulty": "Beginner",
        "content": """<section class="about">
<h2>What is RAG?</h2>
<p>Retrieval Augmented Generation (RAG) combines LLMs with external knowledge retrieval. Instead of relying only on training data, RAG systems fetch relevant documents and include them in the prompt for accurate, up-to-date responses.</p>
<h2>RAG Components</h2>
<p><strong>Document Loading:</strong> Load from PDFs, web pages, databases<br>
<strong>Splitting:</strong> Break documents into chunks<br>
<strong>Embedding:</strong> Convert chunks to vectors<br>
<strong>Storage:</strong> Store in vector database (Pinecone, Chroma, Weaviate)<br>
<strong>Retrieval:</strong> Find relevant chunks for each query<br>
<strong>Generation:</strong> Pass chunks to LLM with the question</p>
<h2>Quick Start</h2>
<p>1. Choose a vector database (Chroma is easiest for local)<br>
2. Install LangChain or LlamaIndex<br>
3. Load and process your documents<br>
4. Create embeddings and store<br>
5. Build retrieval chain<br>
6. Add chat interface</p>
<h2>Best Practices</h2>
<p>Use semantic search, implement hybrid search with keywords, add citation sources, and monitor retrieval quality. Examples below demonstrate different approaches.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What vector database should I use?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "For learning: Chroma (local, free). For production: Pinecone (managed), Weaviate (self-hosted), or pgvector (PostgreSQL extension). Choose based on your scaling needs and infrastructure preferences.",
                },
            },
            {
                "@type": "Question",
                "name": "How do I improve RAG accuracy?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Improve chunking strategy, use hybrid search (semantic + keyword), add reranking, implement query expansion, and fine-tune your prompts. Also ensure high-quality source documents.",
                },
            },
        ],
    },
    {
        "key": "multi-agent-system",
        "title": "How to Build Multi-Agent Systems",
        "description": "Learn to build multi-agent systems where AI agents collaborate. Complete guide with CrewAI, LangChain agents, and custom orchestration patterns.",
        "filter": lambda a: a.get("category") == "multi_agent" or "multi_agent" in a.get("tags", []),
        "difficulty": "Intermediate",
        "content": """<section class="about">
<h2>What are Multi-Agent Systems?</h2>
<p>Multi-agent systems use multiple specialized AI agents working together. Each agent has specific capabilities and can delegate tasks to others. This mirrors how human teams collaborate.</p>
<h2>Common Patterns</h2>
<p><strong>Role-Based:</strong> Each agent has a role (researcher, writer, reviewer)<br>
<strong>Sequential:</strong> Agents pass work in a pipeline<br>
<strong>Hierarchical:</strong> Manager agent delegates to workers<br>
<strong>Debate:</strong> Agents discuss and reach consensus<br>
<strong>Competitive:</strong> Agents compete to find best solution</p>
<h2>Frameworks</h2>
<p>CrewAI: Easiest for role-based systems with clear delegation<br>
LangChain Agents: Flexible with extensive tool ecosystem<br>
AutoGen: Microsoft's conversation-based approach<br>
Custom: Build your own orchestration layer</p>
<h2>Getting Started</h2>
<p>Start with a simple two-agent system: one for research, one for synthesis. Gradually add more agents and complexity. Examples below demonstrate various patterns.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "When should I use multiple agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Use multi-agent systems for complex tasks requiring different skills, when you want clear separation of concerns, or for tasks that benefit from parallel processing. Single agents are better for simple, focused tasks.",
                },
            },
            {
                "@type": "Question",
                "name": "How do agents communicate?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Agents communicate through structured messages, shared context, or a central orchestrator. Frameworks provide different approaches - CrewAI uses hierarchical delegation, AutoGen uses conversations, LangChain uses agent chains.",
                },
            },
        ],
    },
    {
        "key": "local-llm-ollama",
        "title": "How to Run Local LLMs with Ollama",
        "description": "Learn to run LLM agents locally using Ollama. Complete guide for privacy, cost savings, and offline capability.",
        "filter": lambda a: "ollama" in a.get("llm_providers", []) or a.get("supports_local_models", False),
        "difficulty": "Beginner",
        "content": """<section class="about">
<h2>Why Run LLMs Locally?</h2>
<p><strong>Privacy:</strong> Data never leaves your machine<br>
<strong>Cost:</strong> No API fees after initial hardware<br>
<strong>Offline:</strong> Works without internet<br>
<strong>Customization:</strong> Use any open-source model</p>
<h2>What is Ollama?</h2>
<p>Ollama is the easiest way to run LLMs locally. It manages models, provides an API compatible with OpenAI's format, and works on Mac, Linux, and Windows. Models like Llama 3, Mistral, and Phi-3 are available.</p>
<h2>Quick Start</h2>
<p>1. Download Ollama from ollama.ai<br>
2. Run <code>ollama pull llama3</code> (or any model)<br>
3. Run <code>ollama run llama3</code> to chat<br>
4. Use the API at localhost:11434</p>
<h2>Available Models</h2>
<p>Llama 3 (8B, 70B): Meta's excellent general models<br>
Mistral (7B): Strong performance, efficient<br>
Phi-3 (3.8B): Microsoft's small but capable model<br>
Gemma (2B, 7B): Google's lightweight models</p>
<h2>Hardware Requirements</h2>
<p>For 7B models: 8GB VRAM recommended (can work on CPU)<br>
For larger models: 16GB+ VRAM<br>
Quantized models (4-bit) reduce requirements by ~50%</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Can I use Ollama with LangChain?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes! Ollama provides an OpenAI-compatible API. You can use LangChain's ChatOpenAI class with base_url='http://localhost:11434'. Most frameworks that support OpenAI work with Ollama.",
                },
            },
            {
                "@type": "Question",
                "name": "How do local models compare to GPT-4?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "GPT-4 and Claude Opus still outperform local models on complex reasoning. However, Llama 3 8B and Mistral 7B are surprisingly capable for many tasks. Use local for cost/privacy, cloud for quality.",
                },
            },
        ],
    },
    {
        "key": "openai-function-calling",
        "title": "How to Use OpenAI Function Calling",
        "description": "Learn to implement function calling with OpenAI's API. Build agents that can use tools and take actions.",
        "filter": lambda a: "openai" in a.get("llm_providers", []) and ("tool" in a.get("design_pattern", "") or "function" in str(a.get("tags", [])).lower()),
        "difficulty": "Intermediate",
        "content": """<section class="about">
<h2>What is Function Calling?</h2>
<p>Function calling lets LLMs request to run specific functions with structured arguments. The model doesn't execute code directly - it outputs what function to call and with what parameters. Your code executes the function and returns results.</p>
<h2>Use Cases</h2>
<p><strong>Query Databases:</strong> Convert natural language to SQL<br>
<strong>API Calls:</strong> Make external API requests<br>
<strong>Calculations:</strong> Perform accurate math<br>
<strong>Actions:</strong> Send emails, create calendar events<br>
<strong>Data Retrieval:</strong> Fetch specific information</p>
<h2>Basic Pattern</h2>
<p>1. Define functions with schemas (name, description, parameters)<br>
2. Pass functions to ChatCompletion API<br>
3. Check if model wants to call a function<br>
4. Execute the function with provided arguments<br>
5. Return results to model for final response</p>
<h2>Best Practices</h2>
<p>Provide clear function descriptions, use TypeScript-style schema for parameters, handle errors gracefully, and validate arguments before execution.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Is function calling different from tool use?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Function calling is OpenAI's term for tool use. Other providers call it tool use (Anthropic), function calling (Google), or tools (Claude). They all follow similar patterns: define tools, let LLM choose, execute, return results.",
                },
            },
        ],
    },
    {
        "key": "langchain-agents",
        "title": "How to Build Agents with LangChain",
        "description": "Learn to build AI agents using LangChain framework. Complete guide with ReAct agents, tools, and chains.",
        "filter": lambda a: "langchain" in a.get("frameworks", []),
        "difficulty": "Intermediate",
        "content": """<section class="about">
<h2>LangChain Agents</h2>
<p>LangChain agents use LLMs to determine actions, observe results, and iterate until completion. Unlike predefined chains, agents dynamically decide what to do based on the current state.</p>
<h2>Agent Types</h2>
<p><strong>ReAct:</strong> Reasoning + Acting, most common pattern<br>
<strong>OpenAI Functions:</strong> Uses GPT's function calling<br>
<strong>Structured Chat:</strong> For multi-input tools<br>
<strong>Self-Ask with Search:</strong> For complex queries needing research</p>
<h2>Key Components</h2>
<p><strong>Tools:</strong> Functions agents can call (search, calculator, database)<br>
<strong>Toolkits:</strong> Collections of related tools<br>
<strong>Agent Executor:</strong> Runtime that manages agent loops<br>
<strong>Memory:</strong> Maintains conversation context<br>
<strong>Prompt Templates:</strong> Guide agent behavior</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install langchain langchain-openai</code>. Define tools, initialize agent with prompt, and run with executor. Examples below show various patterns.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What's the difference between chains and agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Chains have predefined steps in a fixed sequence. Agents dynamically decide actions based on each step's outcome. Chains are predictable and faster. Agents are flexible and can handle complex, multi-step problems.",
                },
            },
        ],
    },
    {
        "key": "anthropic-claude-agents",
        "title": "How to Build Agents with Anthropic Claude",
        "description": "Learn to build AI agents using Anthropic's Claude API. Tool use, long context, and reliable outputs.",
        "filter": lambda a: "anthropic" in a.get("llm_providers", []),
        "difficulty": "Intermediate",
        "content": """<section class="about">
<h2>Why Build Agents with Claude?</h2>
<p>Claude 3.5 models offer excellent reasoning, 200K token context windows, and strong tool use capabilities. Claude is known for careful, reliable outputs which is crucial for agent systems.</p>
<h2>Claude Tool Use</h2>
<p>Anthropic's tool use (function calling) is highly reliable. Claude excels at understanding when to use tools, extracting proper parameters, and handling tool outputs gracefully.</p>
<h2>Key Features</h2>
<p><strong>Long Context:</strong> 200K tokens for extensive document processing<br>
<strong>Artifacts:</strong> Claude can generate and edit code/artifacts<br>
<strong>Strong Reasoning:</strong> Excellent for complex decision-making<br>
<strong>Reduced Hallucination:</strong> More factual than many alternatives</p>
<h2>Getting Started</h2>
<p>Get API key from console.anthropic.com. Install with <code>pip install anthropic</code>. Define tools in Anthropic's format, pass to messages API, and handle tool_use blocks.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "How does Claude tool use differ from OpenAI?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Claude's tool use is very similar but uses a different API structure. Instead of a separate functions parameter, tools are defined separately and the model returns tool_use content blocks. Both are highly capable - choose based on which model you prefer.",
                },
            },
        ],
    },
]
