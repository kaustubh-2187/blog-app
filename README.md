# AI Blog Writer

**Live Demo:** https://blog-planner-655964848309.us-central1.run.app

An AI-powered blog generation system that uses LangGraph to orchestrate research, planning, and writing workflows. Built as a demonstration of agentic AI workflows with FastAPI and deployed on Google Cloud Run.

---

## Overview

This project generates technical blog posts by combining web research with LLM-based writing. The core workflow uses **LangGraph** to build a multi-step pipeline where each node handles a specific task: routing, research, planning, parallel section writing, and content assembly.

The system decides whether to use web research based on the topic's recency requirements, gathers evidence from the web when needed, creates a structured outline, writes sections in parallel, and optionally generates diagrams using AI image generation.

---

## Architecture

### LangGraph Workflow

The pipeline is implemented as a **StateGraph** with the following nodes:

```
User Topic
    ↓
[Router] → Decides: closed_book | hybrid | open_book
    ↓
[Research] → Tavily web search (if needed)
    ↓
[Orchestrator] → Creates structured blog Plan
    ↓
[Workers] → Write sections in parallel (Map-Reduce)
    ↓
[Reducer Subgraph]
    ├─ Merge sections
    ├─ Decide if images needed
    └─ Generate images (optional)
    ↓
Final Markdown Blog
```

**Key Components:**

- **Router Node** (`blog_app/graph/nodes/router.py`): Analyzes the topic and determines if web research is needed. Returns routing decision and search queries.

- **Research Node** (`blog_app/graph/nodes/research.py`): Executes Tavily searches and structures evidence. No LLM parsing—builds `EvidenceItem` objects directly from API responses.

- **Orchestrator Node** (`blog_app/graph/nodes/orchestrator.py`): Creates a `Plan` with 5-9 tasks using structured output. Each task has a goal, bullet points, target word count, and flags for research/citations/code requirements.

- **Worker Nodes** (`blog_app/graph/nodes/worker.py`): Write individual sections in parallel using LangGraph's `Send` API. Each worker receives one task and relevant evidence.

- **Reducer Subgraph** (`blog_app/graph/nodes/reducer.py`): Merges sections, decides if images improve understanding, generates image prompts, and renders diagrams using Gemini.

**State Management:**

The workflow uses a `TypedDict` state (`blog_app/core/state.py`) that flows through all nodes:

```python
class State(TypedDict):
    topic: str
    mode: str  # closed_book | hybrid | open_book
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Plan
    sections: List[str]
    images_enabled: bool
    final: str
```



## Project Structure

```
blog_app/
├── graph/
│   ├── builder.py              # LangGraph assembly
│   └── nodes/                  # Individual workflow nodes
├── core/
│   ├── state.py               # TypedDict state schema
│   └── schemas.py             # Pydantic models
├── prompts/prompts.py         # System prompts for each node
├── llm/client.py              # ModelLoader with provider switching
└── config/config.yaml         # LLM and pipeline configuration

api/
├── main.py                    # FastAPI app
└── routes/blog.py             # Blog generation endpoints

notebooks/
├── workflow.ipynb             # Original prototype
└── eval.ipynb                 # Evaluation framework

static/                        # Frontend files
sample_data/                   # Demo blogs for initial load
```

---

## Setup

**Prerequisites:**
- Python 3.11+
- API keys: `GOOGLE_API_KEY`, `GROQ_API_KEY`, `TAVILY_API_KEY`

**Local Development:**

```bash
# Clone repo
git clone <repo-url>
cd blog

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Set environment variables
export GOOGLE_API_KEY="your-key"
export GROQ_API_KEY="your-key"
export TAVILY_API_KEY="your-key"

# Run server
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000`

---

## Deployment

**Docker:**

```bash
docker build -t blog-planner .
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  -e TAVILY_API_KEY=$TAVILY_API_KEY \
  blog-planner
```

**Cloud Run:**

The project includes a Jenkins pipeline (`Jenkinsfile`) that:
1. Builds Docker image
2. Pushes to Google Container Registry
3. Deploys to Cloud Run with environment variables


## Configuration

Edit `blog_app/config/config.yaml`:

```yaml
llm:
  provider: "google"  # or "groq"
  google:
    model_name: "gemini-2.5-flash"
    temperature: 0.5
    max_output_tokens: 8192
  groq:
    model_name: "llama-3.3-70b-versatile"
    temperature: 0.5
    max_output_tokens: 8192

research:
  max_queries: 10
  tavily:
    max_results: 2

images_model:
  max_images: 2
  default_size: 512x512
```

---

## API Endpoints

**Generate Blog:**
```bash
POST /api/v1/blog/generate
{
  "topic": "How LangGraph enables agentic workflows",
  "provider": "google",  # optional
  "images_enabled": true
}
```

**Check Status:**
```bash
GET /api/v1/blog/status/{run_id}
```

**Download (ZIP with markdown + images):**
```bash
GET /api/v1/blog/download/{run_id}/markdown
```

**List Past Blogs:**
```bash
GET /api/v1/blog/list
```





---

## Acknowledgments

Built as a learning project to explore LangGraph's capabilities for building production-grade agentic workflows.