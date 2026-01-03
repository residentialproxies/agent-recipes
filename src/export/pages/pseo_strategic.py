"""
Programmatic SEO strategic pages - 20+ high-value landing pages.

Generates:
- Framework pages (8): langchain, crewai, llamaindex, autogen, phidata, dspy, openai-assistants, local-llm
- Category pages (4): rag, multi-agent, chatbot, automation
- Comparison pages (6): framework/framework, provider/provider, concept/concept
- Difficulty pages (3): beginner, intermediate, advanced
"""

from __future__ import annotations

import html
import json
import logging
from collections.abc import Callable
from pathlib import Path

from src.export._utils import _write
from src.export.pages._shared import filter_agents
from src.export.templates import _layout

logger = logging.getLogger(__name__)


# Framework page configurations (8 total)
FRAMEWORK_PAGES = [
    {
        "slug": "langchain-agents",
        "title": "LangChain Agents & Tutorials",
        "heading": "LangChain Agents",
        "description": "Discover LangChain agent examples, tutorials, and templates. Build AI agents with LangChain framework including ReAct agents, tools, chains, and RAG implementations.",
        "icon": "🦜",
        "filter": lambda a: "langchain" in a.get("frameworks", []),
        "intro": """<section class="about">
<h2>Why LangChain?</h2>
<p>LangChain is the most popular framework for building LLM applications. It provides abstractions for agents, chains, tools, memory, and RAG pipelines. With LangChain, you can quickly prototype and productionize AI agents.</p>
<h2>Key Concepts</h2>
<p><strong>Chains:</strong> Sequences of LLM calls<br>
<strong>Agents:</strong> LLMs that decide actions dynamically<br>
<strong>Tools:</strong> Functions agents can call<br>
<strong>Memory:</strong> Conversation state management<br>
<strong>Retrievers:</strong> Fetch relevant context</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install langchain langchain-openai</code>. Browse examples below to see different agent patterns like ReAct agents, OpenAI functions, custom tools, and multi-agent collaboration.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Is LangChain suitable for production?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes, LangChain is production-ready. However, for simple use cases, consider raw APIs to reduce complexity. LangChain shines in complex workflows with multiple components.",
                },
            },
            {
                "@type": "Question",
                "name": "What's the difference between LangChain and LangGraph?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "LangGraph is a newer library for building stateful, multi-actor applications with LLMs. It's better for complex agent workflows. LangChain is the broader framework that includes LangGraph.",
                },
            },
        ],
    },
    {
        "slug": "crewai-tutorials",
        "title": "CrewAI Tutorials & Multi-Agent Examples",
        "heading": "CrewAI Tutorials",
        "description": "Learn CrewAI with step-by-step tutorials. Build multi-agent systems where agents collaborate on complex tasks with role-based delegation.",
        "icon": "👥",
        "filter": lambda a: "crewai" in a.get("frameworks", []),
        "intro": """<section class="about">
<h2>Why CrewAI?</h2>
<p>CrewAI specializes in multi-agent systems where each agent has a specific role. Agents can delegate tasks to each other, collaborate on complex problems, and use tools autonomously. Perfect for automation workflows.</p>
<h2>CrewAI Concepts</h2>
<p><strong>Agents:</strong> Autonomous units with roles, goals, and backstories<br>
<strong>Crews:</strong> Teams of agents working together<br>
<strong>Tasks:</strong> Specific assignments for agents<br>
<strong>Tools:</strong> Functions agents can use<br>
<strong>Processes:</strong> How agents coordinate (sequential, hierarchical)</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install crewai crewai-tools</code>. Define agents with specific roles, create tasks, and assemble them into a crew. Examples below show practical implementations.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "How many agents should I use in a CrewAI crew?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Start with 2-3 agents. Each agent should have a distinct purpose. Common patterns include: researcher + writer, planner + executor, or specialist + reviewer. More agents add complexity.",
                },
            },
        ],
    },
    {
        "slug": "llamaindex-examples",
        "title": "LlamaIndex Examples & RAG Tutorials",
        "heading": "LlamaIndex Examples",
        "description": "Explore LlamaIndex examples for building RAG applications. Data connectors, vector stores, and query engines for knowledge-intensive AI systems.",
        "icon": "🦙",
        "filter": lambda a: "llamaindex" in a.get("frameworks", []),
        "intro": """<section class="about">
<h2>Why LlamaIndex?</h2>
<p>LlamaIndex specializes in connecting LLMs to your data. It provides excellent data loaders, vector store integrations, and advanced retrieval strategies. Best for RAG and knowledge-intensive applications.</p>
<h2>Key Features</h2>
<p><strong>Data Connectors:</strong> Load from PDFs, databases, APIs, and more<br>
<strong>Vector Stores:</strong> 40+ integrations (Pinecone, Chroma, Weaviate)<br>
<strong>Query Engines:</strong> Natural language over your data<br>
<strong>Index Types:</strong> Vector, tree, keyword, and hybrid<br>
<strong>Reranking:</strong> Improve retrieval quality</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install llama-index</code>. Load documents, create an index, and query with natural language. Examples below demonstrate different approaches.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Should I use LlamaIndex or LangChain for RAG?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "LlamaIndex is purpose-built for RAG and excels at data connection and retrieval. LangChain is more general-purpose. Many projects use both: LlamaIndex for data ingestion, LangChain for agent orchestration.",
                },
            },
        ],
    },
    {
        "slug": "autogen-projects",
        "title": "AutoGen Projects & Multi-Agent Examples",
        "heading": "AutoGen Projects",
        "description": "Microsoft AutoGen project examples. Build conversational multi-agent systems where agents collaborate through dialogue to solve complex tasks.",
        "icon": "💬",
        "filter": lambda a: "autogen" in a.get("frameworks", []),
        "intro": """<section class="about">
<h2>Why AutoGen?</h2>
<p>Microsoft's AutoGen enables multi-agent conversations through a simple interface. Agents communicate to solve tasks, with human-in-the-loop options. Excellent for research and complex problem-solving.</p>
<h2>AutoGen Concepts</h2>
<p><strong>Conversable Agents:</strong> Can send/receive messages<br>
<strong>Assistant Agent:</strong> Uses LLM to generate responses<br>
<strong>User Proxy Agent:</strong> Human-in-the-loop or code executor<br>
<strong>Group Chat:</strong> Multi-agent coordination<br>
<strong>Code Execution:</strong> Safe sandbox for running code</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install pyautogen</code>. Create agents, set up conversations, and let them collaborate. Examples below show various patterns.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What makes AutoGen different from CrewAI?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "AutoGen focuses on conversational dynamics between agents. CrewAI focuses on role-based task delegation. AutoGen is great for research and experimentation; CrewAI excels at production automation workflows.",
                },
            },
        ],
    },
    {
        "slug": "phidata-agents",
        "title": "PhiData Agents & Production Examples",
        "heading": "PhiData Agents",
        "description": "PhiData agent examples for production-ready AI systems. Built-in monitoring, evaluation, and deployment tools for serious applications.",
        "icon": "⚙️",
        "filter": lambda a: "phidata" in a.get("frameworks", []),
        "intro": """<section class="about">
<h2>Why PhiData?</h2>
<p>PhiData focuses on production-ready agents with built-in monitoring, evaluation, and deployment capabilities. It's designed for teams building serious AI applications that need observability.</p>
<h2>Key Features</h2>
<p><strong>Monitoring:</strong> Track agent performance and costs<br>
<strong>Evaluation:</strong> Automated testing of agent outputs<br>
<strong>Deployment:</strong> Easy production deployment<br>
<strong>Tools:</strong> Rich library of pre-built tools<br>
<strong>Knowledge Base:</strong> Built-in RAG capabilities</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install phidata</code>. Define assistants, add tools, and deploy. Examples show production-ready patterns.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Is PhiData free?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "PhiData is open-source and free to use. It works with various LLM providers (OpenAI, Anthropic, local), so you'll need to pay for API usage unless using local models.",
                },
            },
        ],
    },
    {
        "slug": "dspy-projects",
        "title": "DSPy Projects & Programmatic Prompting",
        "heading": "DSPy Projects",
        "description": "DSPy examples for programmatic prompting. Build self-improving AI pipelines with automatic prompt optimization and few-shot learning.",
        "icon": "🔧",
        "filter": lambda a: "dspy" in a.get("frameworks", []),
        "intro": """<section class="about">
<h2>Why DSPy?</h2>
<p>DSPy is a framework for algorithmically optimizing LM prompts and weights. Instead of manual prompt engineering, DSPy learns from examples to create optimal prompts. Great for reproducible AI systems.</p>
<h2>Key Concepts</h2>
<p><strong>Signatures:</strong> Define input/output behavior<br>
<strong>Modules:</strong> Composable building blocks<br>
<strong>Teleprompters:</strong> Automatic optimization<br>
<strong>Metrics:</strong> Evaluate output quality<br>
<strong>Optimizers:</strong> Find best prompts automatically</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install dspy-ai</code>. Define signatures, create modules, and let DSPy optimize. Examples show various use cases.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "When should I use DSPy instead of LangChain?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Use DSPy when you want automated prompt optimization and reproducible results. Use LangChain for rapid prototyping and when you need extensive tool integrations. They can also work together.",
                },
            },
        ],
    },
    {
        "slug": "openai-assistants",
        "title": "OpenAI Assistants API Examples",
        "heading": "OpenAI Assistants",
        "description": "OpenAI Assistants API examples. Build stateful AI assistants with code interpretation, file search, and custom tools using OpenAI's managed service.",
        "icon": "🤖",
        "filter": lambda a: "openai" in a.get("llm_providers", [])
        and ("assistant" in str(a.get("tags", [])).lower() or "assistant" in str(a.get("description", "")).lower()),
        "intro": """<section class="about">
<h2>Why OpenAI Assistants?</h2>
<p>The OpenAI Assistants API provides a managed service for building stateful AI assistants. Handle threads, memory, code execution, and file search without managing infrastructure.</p>
<h2>Key Features</h2>
<p><strong>Threads:</strong> Persistent conversation state<br>
<strong>Code Interpreter:</strong> Execute Python code safely<br>
<strong>File Search:</strong> Query uploaded documents<br>
<strong>Function Calling:</strong> Connect to external APIs<br>
<strong>Streaming:</strong> Real-time responses</p>
<h2>Getting Started</h2>
<p>Use the OpenAI Python SDK v1.0+. Create an assistant, add tools, and create threads. Examples below show various patterns.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What's the difference between Assistants API and Chat Completions?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Assistants API manages conversation state, files, and tools for you. Chat Completions is stateless and you manage everything. Assistants is easier for complex applications; Chat Completions gives more control.",
                },
            },
        ],
    },
    {
        "slug": "local-llm-agents",
        "title": "Local LLM Agents & Privacy-First Examples",
        "heading": "Local LLM Agents",
        "description": "Run AI agents locally with Ollama, Llama, Mistral, and other open-source models. Privacy-first, cost-effective alternatives to cloud APIs.",
        "icon": "🏠",
        "filter": lambda a: a.get("supports_local_models", False)
        or "ollama" in a.get("llm_providers", [])
        or "local" in a.get("llm_providers", []),
        "intro": """<section class="about">
<h2>Why Run LLMs Locally?</h2>
<p><strong>Privacy:</strong> Data never leaves your machine<br>
<strong>Cost:</strong> No API fees after initial hardware<br>
<strong>Offline:</strong> Works without internet<br>
<strong>Customization:</strong> Use any open-source model</p>
<h2>Popular Options</h2>
<p><strong>Ollama:</strong> Easiest way to run local LLMs<br>
<strong>Llama 3:</strong> Meta's excellent open models<br>
<strong>Mistral:</strong> Strong performance, efficient<br>
<strong>Phi-3:</strong> Microsoft's small but capable model</p>
<h2>Hardware Requirements</h2>
<p>For 7B models: 8GB VRAM recommended. For larger models: 16GB+ VRAM. CPU-only is possible but slow. Quantized models (4-bit) reduce requirements significantly.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Are local models good enough for production?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "For many tasks, yes. Llama 3 8B and Mistral 7B are excellent. For complex reasoning, GPT-4/Claude Opus still lead. Consider hybrid: local for simple tasks, cloud for complex ones.",
                },
            },
        ],
    },
]

# Category pages (4 total) - RAG, Multi-Agent, Chatbot, Automation
CATEGORY_PAGES = [
    {
        "slug": "rag-tutorials",
        "title": "RAG Tutorials & Retrieval Augmented Generation",
        "heading": "RAG Tutorials",
        "description": "Complete RAG tutorials for building Retrieval Augmented Generation systems. Learn vector databases, document processing, and LLM integration with examples.",
        "icon": "📚",
        "filter": lambda a: a.get("category") == "rag",
        "intro": """<section class="about">
<h2>What is RAG?</h2>
<p>Retrieval Augmented Generation (RAG) combines LLMs with external knowledge retrieval. Instead of relying only on training data, RAG systems fetch relevant documents and include them in the prompt for accurate, up-to-date responses.</p>
<h2>RAG Pipeline Components</h2>
<p><strong>Document Loading:</strong> Load from PDFs, web pages, databases<br>
<strong>Splitting:</strong> Break documents into chunks<br>
<strong>Embedding:</strong> Convert chunks to vectors<br>
<strong>Storage:</strong> Store in vector database<br>
<strong>Retrieval:</strong> Find relevant chunks for queries<br>
<strong>Generation:</strong> Pass chunks to LLM</p>
<h2>Popular Vector Databases</h2>
<p>Chroma (local, free), Pinecone (managed), Weaviate (self-hosted), pgvector (PostgreSQL), Qdrant (open-source)</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What vector database should I use for RAG?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "For learning: Chroma (local, free). For production: Pinecone (managed), Weaviate (self-hosted), or pgvector (PostgreSQL). Choose based on scaling needs and infrastructure preferences.",
                },
            },
            {
                "@type": "Question",
                "name": "How do I improve RAG accuracy?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Improve chunking strategy, use hybrid search (semantic + keyword), add reranking, implement query expansion, and fine-tune prompts. Also ensure high-quality source documents.",
                },
            },
        ],
    },
    {
        "slug": "multi-agent-systems",
        "title": "Multi-Agent Systems & Orchestration",
        "heading": "Multi-Agent Systems",
        "description": "Multi-agent system tutorials and examples. Learn to build AI agents that collaborate, delegate tasks, and solve complex problems together.",
        "icon": "🧩",
        "filter": lambda a: a.get("category") == "multi_agent",
        "intro": """<section class="about">
<h2>What are Multi-Agent Systems?</h2>
<p>Multi-agent systems use multiple specialized AI agents working together. Each agent has specific capabilities and can delegate tasks to others. This mirrors how human teams collaborate.</p>
<h2>Common Patterns</h2>
<p><strong>Role-Based:</strong> Each agent has a specific role<br>
<strong>Sequential:</strong> Agents pass work in a pipeline<br>
<strong>Hierarchical:</strong> Manager agent delegates to workers<br>
<strong>Debate:</strong> Agents discuss and reach consensus<br>
<strong>Competitive:</strong> Agents compete to find best solution</p>
<h2>Frameworks for Multi-Agent</h2>
<p>CrewAI: Role-based systems with clear delegation<br>
LangChain Agents: Flexible with extensive tools<br>
AutoGen: Conversation-based approach<br>
Custom: Build your own orchestration layer</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "When should I use multiple agents instead of one?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Use multi-agent systems for complex tasks requiring different skills, when you want clear separation of concerns, or for tasks that benefit from parallel processing. Single agents are better for simple, focused tasks.",
                },
            },
        ],
    },
    {
        "slug": "chatbot-examples",
        "title": "AI Chatbot Examples & Tutorials",
        "heading": "Chatbot Examples",
        "description": "AI chatbot examples with memory, context, and personality. Build conversational AI with LangChain, OpenAI, Anthropic, and more.",
        "icon": "💬",
        "filter": lambda a: a.get("category") == "chatbot",
        "intro": """<section class="about">
<h2>Building AI Chatbots</h2>
<p>Modern AI chatbots go beyond simple question-answering. They maintain conversation history, understand context, handle multiple topics, and can access external tools and data.</p>
<h2>Key Chatbot Features</h2>
<p><strong>Memory:</strong> Remember conversation history<br>
<strong>Context:</strong> Understand user intent<br>
<strong>Personality:</strong> Consistent tone and style<br>
<strong>Tools:</strong> Access external data and APIs<br>
<strong>Fallback:</strong> Handle unclear requests gracefully</p>
<h2>Chatbot Patterns</h2>
<p>Simple Q&A, RAG-enhanced (knowledge base), Tool-using (can take actions), Multi-agent (specialized sub-agents), Voice-enabled (speech I/O)</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "How do I add memory to my chatbot?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Use a message history buffer to store past exchanges. LangChain provides memory types like ConversationBufferMemory, ConversationSummaryMemory, and ConversationTokenBufferMemory. For production, consider a database-backed store.",
                },
            },
        ],
    },
    {
        "slug": "automation-agents",
        "title": "AI Automation Agents & Workflow Examples",
        "heading": "Automation Agents",
        "description": "Automation agent examples for business workflows. Connect to APIs, automate tasks, and build AI-powered workflow automation.",
        "icon": "⚙️",
        "filter": lambda a: a.get("category") == "automation",
        "intro": """<section class="about">
<h2>AI Automation Agents</h2>
<p>Automation agents use AI to perform tasks end-to-end. They can read emails, update databases, call APIs, make decisions, and coordinate complex workflows without human intervention.</p>
<h2>Common Use Cases</h2>
<p><strong>Email Automation:</strong> Sort, categorize, respond<br>
<strong>Data Entry:</strong> Extract and input information<br>
<strong>Report Generation:</strong> Create summaries and reports<br>
<strong>Task Coordination:</strong> Orchestrate multiple tools<br>
<strong>Monitoring:</strong> Detect and respond to events</p>
<h2>Integration Patterns</h2>
<p>Webhooks, API calls, Zapier/Make integrations, scheduled jobs, event-driven triggers, human-in-the-loop approval</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "How do I connect AI agents to business tools?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Most business tools provide APIs. Use function calling to let agents make API requests. For no-code integration, platforms like Zapier and Make can connect agents to hundreds of services.",
                },
            },
        ],
    },
]

# Comparison pages (6 total)
COMPARISON_PAGES = [
    {
        "slug": "langchain-vs-llamaindex",
        "title": "LangChain vs LlamaIndex Comparison",
        "heading": "LangChain vs LlamaIndex",
        "description": "Compare LangChain and LlamaIndex frameworks. Understand their differences, strengths, and when to use each for building AI applications.",
        "icon": "📊",
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
<h2>Key Differences</h2>
<p><strong>Focus:</strong> LangChain = general framework, LlamaIndex = RAG specialist<br>
<strong>Ecosystem:</strong> LangChain has more integrations, LlamaIndex deeper data connectors<br>
<strong>Learning Curve:</strong> LangChain = steeper, LlamaIndex = gentler for RAG</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Can I use LangChain and LlamaIndex together?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes! They work well together. Use LlamaIndex for data ingestion and retrieval, then pass results to LangChain agents for reasoning and action. This combines LlamaIndex's RAG strengths with LangChain's agent capabilities.",
                },
            },
            {
                "@type": "Question",
                "name": "Which has better performance?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Both are actively optimized. LangChain has more abstraction overhead while LlamaIndex is lighter for pure RAG. Choose based on your use case, not perceived performance. For RAG-heavy apps, LlamaIndex may be more efficient.",
                },
            },
        ],
    },
    {
        "slug": "crewai-vs-autogen",
        "title": "CrewAI vs AutoGen Multi-Agent Comparison",
        "heading": "CrewAI vs AutoGen",
        "description": "Compare CrewAI and AutoGen for multi-agent systems. Understand their approaches to agent collaboration and orchestration.",
        "icon": "📊",
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
<p><strong>Approach:</strong> CrewAI = role-based delegation, AutoGen = conversational dynamics<br>
<strong>Best For:</strong> CrewAI = production automation, AutoGen = research/experimentation<br>
<strong>Mental Model:</strong> CrewAI = team with roles, AutoGen = conversation between agents</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Which is easier for beginners?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "CrewAI's role-based approach is more intuitive for many beginners. The concept of agents with roles is easy to understand. AutoGen's conversation model is powerful but may require more experimentation to master.",
                },
            },
        ],
    },
    {
        "slug": "openai-vs-anthropic",
        "title": "OpenAI vs Anthropic Claude Comparison",
        "heading": "OpenAI vs Anthropic",
        "description": "Compare OpenAI GPT and Anthropic Claude for AI agents. Pricing, capabilities, and best use cases for each provider.",
        "icon": "📊",
        "left": "OpenAI",
        "right": "Anthropic",
        "left_filter": lambda a: "openai" in a.get("llm_providers", []),
        "right_filter": lambda a: "anthropic" in a.get("llm_providers", []),
        "content": """<section class="about">
<h2>OpenAI GPT Overview</h2>
<p>OpenAI offers GPT-4, GPT-4o, and GPT-3.5 with excellent function calling, vision capabilities, and the Assistants API. Largest ecosystem and tool support.</p>
<h2>Anthropic Claude Overview</h2>
<p>Claude 3.5 Haiku, Sonnet, and Opus offer strong reasoning, 200K context windows, and careful outputs. Known for reduced hallucination and excellent for analysis tasks.</p>
<h2>Decision Factors</h2>
<p><strong>Ecosystem:</strong> OpenAI has more integrations<br>
<strong>Context:</strong> Claude offers larger windows (200K)<br>
<strong>Reasoning:</strong> Both strong, Claude often more careful<br>
<strong>Vision:</strong> OpenAI GPT-4o excels<br>
<strong>Pricing:</strong> Varies by model and usage</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Which has better function calling?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Both have excellent function calling. OpenAI's implementation is more mature with broader tool support. Claude 3.5 has competitive function calling with often better reliability. Choose based on which model you prefer overall.",
                },
            },
            {
                "@type": "Question",
                "name": "How do context windows compare?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Claude offers 200K tokens context. GPT-4 Turbo offers 128K tokens. Both support large document analysis. Claude's larger window can be advantageous for extensive document processing and long conversations.",
                },
            },
        ],
    },
    {
        "slug": "rag-vs-vector-search",
        "title": "RAG vs Vector Search Comparison",
        "heading": "RAG vs Vector Search",
        "description": "Compare RAG (Retrieval Augmented Generation) with pure vector search. Understand when to use each approach for your application.",
        "icon": "📊",
        "left": "RAG",
        "right": "Vector Search",
        "left_filter": lambda a: a.get("category") == "rag",
        "right_filter": lambda a: "vector" in str(a.get("tags", [])).lower() or "search" in str(a.get("description", "")).lower(),
        "content": """<section class="about">
<h2>Vector Search Overview</h2>
<p>Vector search finds similar items based on semantic meaning. It returns raw results ranked by similarity. Great for document search, recommendations, and finding related content.</p>
<h2>RAG Overview</h2>
<p>RAG combines vector search with LLM generation. Retrieved context is passed to an LLM to generate contextual, natural language responses. Better for question-answering and explanation.</p>
<h2>When to Use Each</h2>
<p><strong>Vector Search:</strong> When users want to browse results, compare options, or explore content<br>
<strong>RAG:</strong> When users want answers, explanations, or synthesized information<br>
<strong>Hybrid:</strong> Show retrieved results with AI-generated summary</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Is RAG always better than vector search?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "No. RAG adds latency and cost. For search results pages, e-commerce, or any case where users want to see options, pure vector search is better. Use RAG when you need synthesized answers or explanations.",
                },
            },
        ],
    },
    {
        "slug": "sync-vs-async-agents",
        "title": "Synchronous vs Asynchronous AI Agents",
        "heading": "Sync vs Async Agents",
        "description": "Compare synchronous and asynchronous AI agent patterns. Understand performance, scalability, and use cases for each approach.",
        "icon": "📊",
        "left": "Synchronous",
        "right": "Asynchronous",
        "left_filter": lambda a: "sync" in str(a.get("tags", [])).lower() or "real-time" in str(a.get("description", "")).lower(),
        "right_filter": lambda a: "async" in str(a.get("tags", [])).lower() or "background" in str(a.get("description", "")).lower(),
        "content": """<section class="about">
<h2>Synchronous Agents</h2>
<p>Synchronous agents process requests immediately and wait for completion before responding. Simpler to implement and debug. Best for interactive applications where users wait for results.</p>
<h2>Asynchronous Agents</h2>
<p>Asynchronous agents queue tasks and process them in the background. Better for long-running tasks, high-volume processing, and when immediate response isn't required.</p>
<h2>When to Use Each</h2>
<p><strong>Sync:</strong> Chat interfaces, real-time interactions, simple workflows<br>
<strong>Async:</strong> Batch processing, long-running tasks, high-throughput APIs, scheduled jobs</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "How do I implement async AI agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Use task queues (Celery, BullMQ), message brokers (RabbitMQ, Kafka), or managed services (AWS SQS, Google Cloud Tasks). The agent picks up tasks, processes them, and stores results. Users poll or get notified when complete.",
                },
            },
        ],
    },
    {
        "slug": "local-vs-cloud-llm",
        "title": "Local vs Cloud LLMs Comparison",
        "heading": "Local vs Cloud LLMs",
        "description": "Compare running LLMs locally vs using cloud APIs. Privacy, cost, performance, and use case considerations.",
        "icon": "📊",
        "left": "Local LLMs",
        "right": "Cloud LLMs",
        "left_filter": lambda a: a.get("supports_local_models", False)
        or "ollama" in a.get("llm_providers", [])
        or "local" in a.get("llm_providers", []),
        "right_filter": lambda a: any(
            p in ["openai", "anthropic", "google", "cohere"] for p in a.get("llm_providers", [])
        ),
        "content": """<section class="about">
<h2>Local LLMs (Ollama, Llama, Mistral)</h2>
<p>Run models on your hardware for complete privacy, no API costs, and offline capability. Requires GPU for good performance. Models like Llama 3, Mistral, and Phi-3 are surprisingly capable.</p>
<h2>Cloud LLMs (OpenAI, Anthropic, Google)</h2>
<p>Best-in-class models, instant scaling, zero infrastructure. Pay per usage with predictable costs. GPT-4 and Claude Opus still outperform most open models.</p>
<h2>Decision Framework</h2>
<p>Use local for: sensitive data, cost control, offline needs, privacy requirements<br>
Use cloud for: best quality, speed of development, model quality matters more than cost</p>
<h2>Hybrid Approach</h2>
<p>Many production systems use both: local models for simple tasks and sensitive data, cloud models for complex reasoning. This optimizes both cost and quality.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What hardware do I need for local LLMs?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "For 7B models: 8GB GPU VRAM is comfortable. For 13B+: 16GB+ recommended. CPU-only is possible but slow. Quantized models (4-bit) reduce requirements significantly. Ollama makes setup easy on Mac, Linux, and Windows.",
                },
            },
            {
                "@type": "Question",
                "name": "Are local models good enough for production?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "It depends on your use case. Llama 3 8B and Mistral 7B are excellent for many tasks. For complex reasoning, GPT-4/Claude Opus still lead. Hybrid architectures often work best: local for simple queries, cloud for complex ones.",
                },
            },
        ],
    },
]

# Difficulty pages (3 total)
DIFFICULTY_PAGES = [
    {
        "slug": "beginner-ai-projects",
        "title": "Beginner AI Projects & Tutorials",
        "heading": "Beginner AI Projects",
        "description": "Start your AI journey with beginner-friendly projects. Simple chatbots, basic RAG, and easy-to-understand agent examples.",
        "icon": "🌱",
        "filter": lambda a: a.get("complexity") == "beginner",
        "intro": """<section class="about">
<h2>Starting with AI Agents</h2>
<p>These beginner projects are designed for developers new to AI agents. Each example includes clear documentation, step-by-step setup, and minimal dependencies.</p>
<h2>What You'll Learn</h2>
<p><strong>Basics:</strong> How LLM APIs work<br>
<strong>Prompting:</strong> Effective prompt design<br>
<strong>Simple Agents:</strong> Basic agent patterns<br>
<strong>Tools:</strong> Using pre-built components<br>
<strong>Deployment:</strong> Running your first agent</p>
<h2>Prerequisites</h2>
<p>Basic Python knowledge, understanding of APIs, and a code editor. No AI/ML experience required. Start with projects that match your interests.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "Do I need machine learning experience?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "No. These projects use pre-trained models via APIs. You don't need to train models or have ML background. Basic programming skills and understanding of APIs are sufficient.",
                },
            },
        ],
    },
    {
        "slug": "intermediate-ai-tutorials",
        "title": "Intermediate AI Tutorials & Projects",
        "heading": "Intermediate AI Tutorials",
        "description": "Expand your AI skills with intermediate projects. RAG systems, multi-agent patterns, and production-ready implementations.",
        "icon": "🚀",
        "filter": lambda a: a.get("complexity") == "intermediate",
        "intro": """<section class="about">
<h2>Intermediate AI Development</h2>
<p>These projects assume you're comfortable with basic LLM APIs and simple agents. You'll learn advanced patterns like RAG, tool use, and multi-agent coordination.</p>
<h2>What You'll Learn</h2>
<p><strong>RAG:</strong> Building knowledge-aware agents<br>
<strong>Tools:</strong> Creating custom function calling<br>
<strong>Multi-Agent:</strong> Coordinating multiple agents<br>
<strong>Memory:</strong> Conversation state management<br>
<strong>Production:</strong> Deployment best practices</p>
<h2>Prerequisites</h2>
<p>Experience with LLM APIs, Python development, and basic agent concepts. Familiarity with vector databases and embeddings is helpful but not required.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What skills should I have before attempting these?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "You should be comfortable with Python, understand basic LLM API usage, and have built at least one simple AI project. Familiarity with async programming, databases, and APIs will be helpful.",
                },
            },
        ],
    },
    {
        "slug": "advanced-agent-patterns",
        "title": "Advanced Agent Patterns & Projects",
        "heading": "Advanced Agent Patterns",
        "description": "Master advanced AI agent architectures. Complex multi-agent systems, production deployments, and cutting-edge patterns.",
        "icon": "🏆",
        "filter": lambda a: a.get("complexity") == "advanced",
        "intro": """<section class="about">
<h2>Advanced Agent Development</h2>
<p>These projects showcase sophisticated AI architectures and production deployments. Learn from real-world implementations handling complex tasks at scale.</p>
<h2>What You'll Learn</h2>
<p><strong>Orchestration:</strong> Complex multi-agent systems<br>
<strong>Optimization:</strong> Performance and cost tuning<br>
<strong>Reliability:</strong> Error handling and fallbacks<br>
<strong>Scaling:</strong> Production deployment patterns<br>
<strong>Advanced Patterns:</strong> Reflection, planning, self-improvement</p>
<h2>Prerequisites</h2>
<p>Strong Python skills, experience with RAG and multi-agent systems, understanding of production deployment, and familiarity with monitoring/observability concepts.</p>
</section>""",
        "faqs": [
            {
                "@type": "Question",
                "name": "What makes an agent system 'advanced'?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Advanced systems typically involve multiple agents, complex orchestration, production concerns (monitoring, scaling), sophisticated error handling, or novel architectures like self-improving agents.",
                },
            },
        ],
    },
]


def _render_page_card(agent: dict) -> str:
    """Render a single agent card for listing pages."""
    name = html.escape(agent.get("name", "Untitled"))
    desc = html.escape((agent.get("description") or "")[:120])
    href = f"/agents/{html.escape(agent.get('id', ''))}/"
    badges = []

    if agent.get("frameworks"):
        badges.append(html.escape(agent["frameworks"][0]))
    if agent.get("llm_providers"):
        badges.append(html.escape(agent["llm_providers"][0]))
    if isinstance(agent.get("stars"), int):
        badges.append(f"⭐ {agent['stars']:,}")

    badge_html = "".join(f'<span class="badge">{b}</span>' for b in badges[:2])

    return f'''<a class="card" href="{href}">
  <div class="card-title">{name}</div>
  <div class="card-desc">{desc}</div>
  <div class="card-badges">{badge_html}</div>
</a>'''


def _render_pseo_framework_page(
    config: dict,
    agents: list[dict],
    *,
    base_url: str | None,
    site_url: str,
) -> str:
    """Render a framework-specific pSEO page."""
    slug = config["slug"]
    icon = config["icon"]
    title = config["title"]
    heading = config["heading"]
    description = config["description"]
    intro = config["intro"]
    faqs = config.get("faqs", [])

    count = len(agents)

    # Build agent cards
    cards = "".join(_render_page_card(a) for a in agents[:50])

    # Build stats
    frameworks = {}
    providers = {}
    for a in agents:
        for fw in a.get("frameworks", []):
            frameworks[fw] = frameworks.get(fw, 0) + 1
        for p in a.get("llm_providers", []):
            providers[p] = providers.get(p, 0) + 1

    fw_stats = " ".join(
        f'<span class="chip">{html.escape(k.title())} ({v})</span>'
        for k, v in sorted(frameworks.items(), key=lambda x: -x[1])[:5]
    )
    provider_stats = " ".join(
        f'<span class="chip">{html.escape(k.title())} ({v})</span>'
        for k, v in sorted(providers.items(), key=lambda x: -x[1])[:5]
    )

    # FAQ HTML
    faq_html = ""
    if faqs:
        faq_items = ""
        for faq in faqs:
            question = html.escape(faq.get("name", ""))
            answer = html.escape(faq.get("acceptedAnswer", {}).get("text", ""))
            faq_items += f"""
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>"""
        faq_html = f"""
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>"""

    # Schema
    schema_list = [
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faqs,
        },
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": heading,
            "description": description,
            "url": f"{site_url}/{slug}/",
        },
    ]
    combined_schema = json.dumps(schema_list, indent=2) if base_url else ""

    # Build related links
    related_links = [
        ("All Tutorials", "/how-to/"),
        ("Compare Frameworks", "/compare/"),
        ("All Agents", "/"),
    ]
    related_html = "".join(
        f'<a class="chip" href="{href}">{html.escape(text)}</a>' for text, href in related_links
    )

    body = f"""
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li aria-current="page">{html.escape(heading)}</li>
  </ol>
</nav>

<section class="hero">
  <h1>{icon} {html.escape(heading)}</h1>
  <p class="lead">{html.escape(description)}</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{count}</div><div class="stat-label">examples</div></div>
  </div>
</section>

{intro}

<section>
  <h2>Tech Stack</h2>
  <div class="chips">{fw_stats}</div>
</section>

<section>
  <h2>Related Topics</h2>
  <div class="chips">{related_html}</div>
</section>

<section>
  <h2>All {html.escape(heading)} Examples</h2>
  <div class="grid">
    {cards}
  </div>
</section>

{faq_html}

<section class="about">
  <p><a class="muted" href="/">&larr; Back to all agents</a></p>
</section>
"""

    return _layout(
        title,
        f"{description} Browse {count} examples with code and setup.",
        body,
        canonical=f"{site_url}/{slug}/" if base_url else None,
        asset_prefix="../",
        schema_json=combined_schema,
    )


def _render_pseo_comparison_page(
    config: dict,
    left_agents: list[dict],
    right_agents: list[dict],
    *,
    base_url: str | None,
    site_url: str,
) -> str:
    """Render a comparison pSEO page."""
    slug = config["slug"]
    icon = config["icon"]
    title = config["title"]
    heading = config["heading"]
    description = config["description"]
    content = config["content"]
    faqs = config.get("faqs", [])

    left_count = len(left_agents)
    right_count = len(right_agents)
    left_name = config["left"]
    right_name = config["right"]

    # Build cards
    left_cards = "".join(_render_page_card(a) for a in left_agents[:20])
    right_cards = "".join(_render_page_card(a) for a in right_agents[:20])

    # FAQ HTML
    faq_html = ""
    if faqs:
        faq_items = ""
        for faq in faqs:
            question = html.escape(faq.get("name", ""))
            answer = html.escape(faq.get("acceptedAnswer", {}).get("text", ""))
            faq_items += f"""
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>"""
        faq_html = f"""
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>"""

    # Schema
    schema_list = [
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faqs,
        },
    ]
    combined_schema = json.dumps(schema_list, indent=2) if base_url else ""

    body = f"""
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/compare/">Comparisons</a></li>
    <li aria-current="page">{html.escape(heading)}</li>
  </ol>
</nav>

<section class="hero">
  <h1>{icon} {html.escape(heading)}</h1>
  <p class="lead">{html.escape(description)}</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{left_count}</div><div class="stat-label">{html.escape(left_name)}</div></div>
    <div class="stat"><div class="stat-num">{right_count}</div><div class="stat-label">{html.escape(right_name)}</div></div>
  </div>
</section>

{content}

<section>
  <h2>{html.escape(left_name)} Examples</h2>
  <div class="grid">
    {left_cards}
  </div>
</section>

<section>
  <h2>{html.escape(right_name)} Examples</h2>
  <div class="grid">
    {right_cards}
  </div>
</section>

{faq_html}

<section class="about">
  <p><a class="muted" href="/compare/">&larr; Back to comparisons</a> | <a class="muted" href="/">Back to home</a></p>
</section>
"""

    return _layout(
        title,
        f"{description} Compare {left_count} {left_name} vs {right_count} {right_name} examples.",
        body,
        canonical=f"{site_url}/{slug}/" if base_url else None,
        asset_prefix="../../",
        schema_json=combined_schema,
    )


def generate_pseo_framework_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: str | None,
    site_url: str,
    additional_urls: list[str],
) -> None:
    """Generate all framework-specific pSEO pages."""
    for config in FRAMEWORK_PAGES:
        try:
            matched = filter_agents(agents, config["filter"])
            if not matched:
                logger.warning("No agents found for framework page: %s", config["slug"])
                continue

            html_content = _render_pseo_framework_page(
                config, matched, base_url=base_url, site_url=site_url
            )
            _write(output_dir / config["slug"] / "index.html", html_content)
            additional_urls.append(f"{site_url}/{config['slug']}/")
            logger.info("Generated framework page: %s (%d agents)", config["slug"], len(matched))
        except Exception as e:
            logger.error("Error generating framework page %s: %s", config["slug"], e)


def generate_pseo_category_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: str | None,
    site_url: str,
    additional_urls: list[str],
) -> None:
    """Generate all category-specific pSEO pages."""
    for config in CATEGORY_PAGES:
        try:
            matched = filter_agents(agents, config["filter"])
            if not matched:
                logger.warning("No agents found for category page: %s", config["slug"])
                continue

            html_content = _render_pseo_framework_page(
                config, matched, base_url=base_url, site_url=site_url
            )
            _write(output_dir / config["slug"] / "index.html", html_content)
            additional_urls.append(f"{site_url}/{config['slug']}/")
            logger.info("Generated category page: %s (%d agents)", config["slug"], len(matched))
        except Exception as e:
            logger.error("Error generating category page %s: %s", config["slug"], e)


def generate_pseo_comparison_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: str | None,
    site_url: str,
    additional_urls: list[str],
) -> None:
    """Generate all comparison pSEO pages."""
    for config in COMPARISON_PAGES:
        try:
            left_matched = filter_agents(agents, config["left_filter"])
            right_matched = filter_agents(agents, config["right_filter"])

            if not left_matched and not right_matched:
                logger.warning("No agents found for comparison page: %s", config["slug"])
                continue

            html_content = _render_pseo_comparison_page(
                config,
                left_matched,
                right_matched,
                base_url=base_url,
                site_url=site_url,
            )
            _write(output_dir / config["slug"] / "index.html", html_content)
            additional_urls.append(f"{site_url}/{config['slug']}/")
            logger.info(
                "Generated comparison page: %s (%d left, %d right)",
                config["slug"],
                len(left_matched),
                len(right_matched),
            )
        except Exception as e:
            logger.error("Error generating comparison page %s: %s", config["slug"], e)


def generate_pseo_difficulty_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: str | None,
    site_url: str,
    additional_urls: list[str],
) -> None:
    """Generate all difficulty-specific pSEO pages."""
    for config in DIFFICULTY_PAGES:
        try:
            matched = filter_agents(agents, config["filter"])
            if not matched:
                logger.warning("No agents found for difficulty page: %s", config["slug"])
                continue

            html_content = _render_pseo_framework_page(
                config, matched, base_url=base_url, site_url=site_url
            )
            _write(output_dir / config["slug"] / "index.html", html_content)
            additional_urls.append(f"{site_url}/{config['slug']}/")
            logger.info("Generated difficulty page: %s (%d agents)", config["slug"], len(matched))
        except Exception as e:
            logger.error("Error generating difficulty page %s: %s", config["slug"], e)


def generate_all_pseo_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: str | None,
    site_url: str,
    additional_urls: list[str],
) -> None:
    """Generate all strategic pSEO pages (20+ total)."""
    logger.info("Generating strategic pSEO pages...")

    generate_pseo_framework_pages(
        agents, output_dir, base_url=base_url, site_url=site_url, additional_urls=additional_urls
    )
    generate_pseo_category_pages(
        agents, output_dir, base_url=base_url, site_url=site_url, additional_urls=additional_urls
    )
    generate_pseo_comparison_pages(
        agents, output_dir, base_url=base_url, site_url=site_url, additional_urls=additional_urls
    )
    generate_pseo_difficulty_pages(
        agents, output_dir, base_url=base_url, site_url=site_url, additional_urls=additional_urls
    )

    total_pages = (
        len(FRAMEWORK_PAGES) + len(CATEGORY_PAGES) + len(COMPARISON_PAGES) + len(DIFFICULTY_PAGES)
    )
    logger.info("Generated %d strategic pSEO pages", total_pages)
