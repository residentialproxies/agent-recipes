# Agent Navigator - 剩余优化执行计划

## 概述

本文档详细说明了剩余 5 项优化任务的实施步骤、文件变更和测试策略。

---

## P1: 拆分 src/api.py 为 src/api/ 包

### 当前状态

- **文件大小**: 889 行
- **主要内容**: FastAPI 应用、路由、中间件、Pydantic 模型
- **问题**: 单文件过大，职责混杂

### 目标结构

```
src/api/
├── __init__.py          # 导出 create_app, app
├── app.py               # FastAPI 工厂函数 (~150 行)
├── models.py            # Pydantic 模型 (~150 行)
├── middleware.py        # IP 提取、安全头 (~100 行)
├── dependencies.py      # 依赖注入 (~100 行)
└── routes/
    ├── __init__.py      # 导出所有路由
    ├── agents.py        # /v1/agents, /v1/search (~200 行)
    ├── ai.py            # /v1/ai/* (~200 行)
    └── webmanus.py      # /v1/workers, /v1/consult (~200 行)
```

### 详细步骤

#### 步骤 1: 创建 models.py (约 150 行)

```python
# src/api/models.py
"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, Union, List

class SearchRequest(BaseModel):
    q: str = ""
    category: Optional[Union[List[str], str]] = None
    framework: Optional[Union[List[str], str]] = None
    provider: Optional[Union[List[str], str]] = None
    complexity: Optional[Union[List[str], str]] = None
    local_only: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class AISelectRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    max_candidates: int = Field(default=80, ge=10, le=120)
    category: Optional[Union[List[str], str]] = None
    framework: Optional[Union[List[str], str]] = None
    provider: Optional[Union[List[str], str]] = None
    complexity: Optional[Union[List[str], str]] = None

class WebManusConsultRequest(BaseModel):
    # ... 从 api.py 移动

class WebManusRecommendation(BaseModel):
    # ... 从 api.py 移动

class WebManusConsultResponse(BaseModel):
    # ... 从 api.py 移动

class AppState(BaseModel):
    # ... 从 api.py 移动
```

#### 步骤 2: 创建 middleware.py (约 100 行)

```python
# src/api/middleware.py
"""
Middleware functions for security and request processing.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import settings

def _get_client_ip(request: Request) -> str:
    """从 api.py 移动"""
    # 保持现有实现

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """添加安全头的中间件"""
    # 从 api.py 的 create_app 中提取

def setup_cors(app):
    """CORS 配置"""
    # 从 api.py 提取 CORS 设置

def setup_compression(app):
    """GZip 压缩配置"""
    # 从 api.py 提取 GZip 中间件
```

#### 步骤 3: 创建 dependencies.py (约 100 行)

```python
# src/api/dependencies.py
"""
Dependency injection for API endpoints.
"""
from fastapi import Depends
from src.data_store import get_search_engine, load_agents
from src.repository import AgentRepo
from src.security.rate_limit import get_rate_limiter

def get_search_engine_dep():
    """搜索引擎依赖"""
    # 从 api.py 提取

def get_webmanus_repo():
    """WebManus 仓库依赖"""
    # 从 api.py 提取

def get_rate_limiter_dep():
    """速率限制依赖"""
    # 从 api.py 提取

def verify_rate_limit(client_ip: str = Depends(_get_client_ip)):
    """速率检查依赖"""
    # 从 api.py 提取
```

#### 步骤 4: 创建 routes/agents.py (约 200 行)

```python
# src/api/routes/agents.py
"""
Agent search and detail routes.
"""
from fastapi import APIRouter, HTTPException, Query
from src.api.models import SearchRequest
from src.api.dependencies import get_search_engine_dep, verify_rate_limit

router = APIRouter(prefix="/v1/agents", tags=["agents"])

@router.get("")
async def search_agents(
    q: str = "",
    category: str = None,
    # ... 其他参数
):
    """从 api.py /v1/agents 端点移动"""
    pass

@router.get("/{agent_id}")
async def get_agent_detail(agent_id: str):
    """从 api.py /v1/agents/{id} 端点移动"""
    pass

@router.post("/search")
async def post_search(request: SearchRequest):
    """从 api.py POST /v1/search 端点移动"""
    pass
```

#### 步骤 5: 创建 routes/ai.py (约 200 行)

```python
# src/api/routes/ai.py
"""
AI selector routes.
"""
from fastapi import APIRouter
from src.api.models import AISelectRequest

router = APIRouter(prefix="/v1/ai", tags=["ai"])

@router.post("/select")
async def ai_select(request: AISelectRequest):
    """从 api.py /v1/ai/select 端点移动"""
    pass

@router.post("/select/stream")
async def ai_select_stream(request: AISelectRequest):
    """从 api.py /v1/ai/select/stream 端点移动"""
    pass
```

#### 步骤 6: 创建 routes/webmanus.py (约 200 行)

```python
# src/api/routes/webmanus.py
"""
WebManus consultation routes.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/v1/workers", tags=["webmanus"])

@router.get("")
async def list_workers():
    """从 api.py /v1/workers 端点移动"""
    pass

@router.get("/{slug}")
async def get_worker(slug: str):
    """从 api.py /v1/workers/{slug} 端点移动"""
    pass

@router.post("/consult")
async def consult(request):
    """从 api.py /v1/consult 端点移动"""
    pass

@router.post("/consult/stream")
async def consult_stream(request):
    """从 api.py /v1/consult/stream 端点移动"""
    pass
```

#### 步骤 7: 创建新的 app.py (约 150 行)

```python
# src/api/app.py
"""
FastAPI application factory.
"""
from fastapi import FastAPI
from src.api.middleware import setup_cors, setup_compression, SecurityHeadersMiddleware
from src.api.routes import agents, ai, webmanus
from src.config import settings

def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title="Agent Navigator API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 设置中间件
    setup_cors(app)
    setup_compression(app)
    app.add_middleware(SecurityHeadersMiddleware)

    # 注册路由
    app.include_router(agents.router)
    app.include_router(ai.router)
    app.include_router(webmanus.router)

    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app

# 全局 app 实例（向后兼容）
app = create_app()
```

#### 步骤 8: 更新 **init**.py

```python
# src/api/__init__.py
"""
Agent Navigator API Package.

向后兼容: 导出 create_app 和 app
"""
from src.api.app import create_app, app

__all__ = ["create_app", "app"]
```

#### 步骤 9: 保留兼容性包装器

```python
# src/api.py (新 - 向后兼容)
"""
向后兼容入口点。
保留此文件以支持现有导入: from src.api import app
"""
from src.api.app import create_app, app

__all__ = ["create_app", "app"]
```

### 测试策略

```bash
# 运行现有测试确保无破坏
pytest tests/test_api.py -v

# 测试新导入
python3 -c "from src.api import app; print('OK')"
python3 -c "from src.api.app import create_app; print('OK')"

# 测试 API 启动
uvicorn src.api:app --host localhost --port 8000
curl http://localhost:8000/health
```

### 验收标准

- [ ] 所有现有测试通过
- [ ] API 服务正常启动
- [ ] 所有端点响应正常
- [ ] 向后兼容导入有效
- [ ] 代码行数 < 200/文件

---

## P1: 拆分 src/app.py 为 src/ui/ 包

### 当前状态

- **文件大小**: 1008 行
- **主要内容**: Streamlit UI、组件、页面渲染、会话管理
- **问题**: 单文件过大，UI 逻辑混杂

### 目标结构

```
src/ui/
├── __init__.py          # 导出 main
├── app.py               # 主入口 (~100 行)
├── components.py        # 可复用组件 (~250 行)
├── pages.py             # 页面渲染 (~350 行)
├── session.py           # 会话状态管理 (~150 行)
└── styles.py            # CSS/样式 (~100 行)
```

### 详细步骤

#### 步骤 1: 创建 session.py (约 150 行)

```python
# src/ui/session.py
"""
会话状态管理。
"""
from typing import Set, List
import streamlit as st

def get_session_id() -> str:
    """获取/创建会话 ID"""
    # 从 app.py 移动

def get_favorites() -> Set[str]:
    """获取收藏列表"""
    # 从 app.py 移动

def toggle_favorite(agent_id: str) -> None:
    """切换收藏状态"""
    # 从 app.py 移动

def get_recently_viewed() -> List[str]:
    """获取最近查看"""
    # 从 app.py 移动

def add_to_recently_viewed(agent_id: str) -> None:
    """添加到最近查看"""
    # 从 app.py 移动

def is_onboarding_complete() -> bool:
    """检查是否完成引导"""
    # 从 app.py 移动

def mark_onboarding_complete() -> None:
    """标记引导完成"""
    # 从 app.py 移动
```

#### 步骤 2: 创建 components.py (约 250 行)

```python
# src/ui/components.py
"""
可复用 UI 组件。
"""
import streamlit as st
from typing import Optional

def render_agent_card(agent: dict) -> None:
    """渲染单个 agent 卡片"""
    # 从 app.py 移动 render_agent_card

def render_icon(category: str) -> str:
    """获取类别图标"""
    # 从 app.py 移动图标渲染逻辑

def render_badge(text: str, color: str) -> str:
    """渲染徽章"""
    # 从 app.py 移动徽章渲染

def render_mermaid(diagram: str, height: int = 260) -> None:
    """渲染 Mermaid 图表"""
    # 从 app.py 移动

def render_onboarding_tour() -> bool:
    """渲染引导游览"""
    # 从 app.py 移动
```

#### 步骤 3: 创建 pages.py (约 350 行)

```python
# src/ui/pages.py
"""
页面渲染函数。
"""
import streamlit as st
from typing import Optional
from src.search import AgentSearch

def render_search_page(
    search_engine: AgentSearch,
    agents: list[dict],
    agent_by_id: dict[str, dict],
) -> None:
    """渲染搜索页面"""
    # 从 app.py 移动 render_search_page

def render_detail_page(
    agent: dict,
    agents: list[dict],
) -> None:
    """渲染详情页面"""
    # 从 app.py 移动 render_detail_page

def render_ai_selector_hero(agents: list[dict]) -> tuple[bool, str]:
    """渲染 AI 选择器"""
    # 从 app.py 移动 render_ai_selector_hero
```

#### 步骤 4: 创建 styles.py (约 100 行)

```python
# src/ui/styles.py
"""
CSS 样式定义。
"""
import streamlit as st

CUSTOM_CSS = '''
<style>
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  [data-testid="stMetricValue"] { font-size: 1.1rem; }
  /* ... 更多样式 */
</style>
'''

def apply_custom_styles():
    """应用自定义样式"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

MOBILE_CSS = '''
@media (max-width: 768px) {
  .agent-grid { grid-template-columns: 1fr; }
  /* ... 移动端样式 */
}
'''

def apply_mobile_styles():
    """应用移动端样式"""
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
```

#### 步骤 5: 创建新的 app.py (约 100 行)

```python
# src/ui/app.py
"""
Streamlit 应用主入口。
"""
import streamlit as st
from src.config import settings, CATEGORY_ICONS
from src.search import AgentSearch
from src.ui.session import get_session_id, is_onboarding_complete
from src.ui.styles import apply_custom_styles, apply_mobile_styles
from src.ui.pages import render_search_page, render_detail_page, render_ai_selector_hero
from src.ui.components import render_sidebar

def load_agents() -> list[dict]:
    """加载 agents 数据"""
    # 从 app.py 移动

def build_search_engine(agents: list[dict]) -> AgentSearch:
    """构建搜索引擎"""
    # 从 app.py 移动

def main() -> None:
    """主应用入口"""
    # 页面配置
    st.set_page_config(
        page_title="Agent Navigator",
        page_icon="🧭",
        layout="wide",
    )

    # 应用样式
    apply_custom_styles()
    apply_mobile_styles()

    # 初始化会话
    get_session_id()

    # 加载数据
    agents = load_agents()
    search_engine = build_search_engine(agents)
    agent_by_id = {a['id']: a for a in agents}

    # 路由
    query_params = st.query_params
    agent_id = query_params.get("agent")

    if agent_id:
        agent = agent_by_id.get(agent_id)
        if agent:
            render_detail_page(agent, agents)
    else:
        render_search_page(search_engine, agents, agent_by_id)

if __name__ == "__main__":
    main()
```

#### 步骤 6: 更新 **init**.py

```python
# src/ui/__init__.py
"""
Agent Navigator UI Package.
"""
from src.ui.app import main

__all__ = ["main"]
```

#### 步骤 7: 保留兼容性包装器

```python
# src/app.py (新 - 向后兼容)
"""
向后兼容入口点。
streamlit run src/app.py 仍然有效。
"""
from src.ui.app import main

if __name__ == "__main__":
    main()
```

### 测试策略

```bash
# 运行 Streamlit 应用
streamlit run src/app.py

# 测试新入口
streamlit run src/ui/app.py

# 验证所有功能正常
# - 搜索功能
# - 过滤器
# - Agent 详情
# - 收藏功能
# - AI 选择器
```

### 验收标准

- [ ] Streamlit 应用正常启动
- [ ] 所有页面功能正常
- [ ] 会话状态正确保存
- [ ] 向后兼容启动命令有效
- [ ] 代码行数 < 400/文件

---

## P2: 用户持久化账户 (数据库)

### 目标

实现用户账户系统，支持跨会话收藏、搜索历史、偏好设置。

### 技术方案

使用 SQLite 存储用户数据（与现有技术栈一致），支持简单注册/登录。

### 数据库 Schema

```sql
-- users 表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);

-- user_favorites 表
CREATE TABLE user_favorites (
    user_id INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, agent_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- user_search_history 表
CREATE TABLE user_search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    filters TEXT,  -- JSON 格式存储过滤器
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- user_preferences 表
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    preferred_frameworks TEXT,  -- JSON 数组
    preferred_providers TEXT,    -- JSON 数组
    items_per_page INTEGER DEFAULT 20,
    theme TEXT DEFAULT 'auto',
    FOREIGN KEY (user_id) REFERENCES users(id) on DELETE CASCADE
);

-- sessions 表 (可选，用于会话管理)
CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 文件结构

```
src/
├── auth/
│   ├── __init__.py
│   ├── models.py         # User, Session, etc.
│   ├── repository.py     # UserRepository
│   ├── service.py        # AuthService
│   └── security.py       # 密码哈希、token 生成
├── api/
│   └── routes/
│       └── auth.py       # 登录/注册/登出 API
└── ui/
    └── pages/
        └── auth.py       # 登录/注册 UI
```

### 实施步骤

#### 步骤 1: 创建认证模块

```python
# src/auth/__init__.py
"""
用户认证和授权模块。
"""
from src.auth.service import AuthService
from src.auth.repository import UserRepository
from src.auth.models import User, Session, CreateUser, LoginRequest

__all__ = ["AuthService", "UserRepository", "User", "Session"]
```

#### 步骤 2: 实现数据模型

```python
# src/auth/models.py
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None

@dataclass
class CreateUser:
    username: str
    email: str
    password: str

@dataclass
class LoginRequest:
    email: str
    password: str

@dataclass
class Session:
    token: str
    user_id: int
    expires_at: datetime
```

#### 步骤 3: 实现仓库层

```python
# src/auth/repository.py
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional
from src.auth.models import User, CreateUser

class UserRepository:
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        # 创建上述所有表

    def create_user(self, data: CreateUser) -> User:
        """创建新用户"""
        # 密码哈希、插入数据库

    def find_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查找用户"""

    def find_by_id(self, user_id: int) -> Optional[User]:
        """通过 ID 查找用户"""

    def verify_password(self, email: str, password: str) -> bool:
        """验证密码"""

    # ... favorites, history, preferences 方法
```

#### 步骤 4: 实现服务层

```python
# src/auth/service.py
import secrets
import time
from datetime import datetime, timedelta
from src.auth.repository import UserRepository
from src.auth.models import User, Session, CreateUser, LoginRequest

class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def register(self, data: CreateUser) -> User:
        """注册新用户"""
        # 验证输入、创建用户

    def login(self, data: LoginRequest) -> Optional[Session]:
        """用户登录"""
        # 验证凭据、创建会话

    def logout(self, token: str) -> None:
        """用户登出"""

    def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""

    def add_favorite(self, user_id: int, agent_id: str) -> None:
        """添加收藏"""

    def remove_favorite(self, user_id: int, agent_id: str) -> None:
        """移除收藏"""

    def get_favorites(self, user_id: int) -> List[str]:
        """获取用户收藏列表"""

    def save_search(self, user_id: int, query: str, filters: dict) -> None:
        """保存搜索历史"""

    def get_search_history(self, user_id: int, limit: int = 10) -> List[dict]:
        """获取搜索历史"""
```

#### 步骤 5: API 路由

```python
# src/api/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends, Cookie
from src.auth.service import AuthService
from src.auth.models import CreateUser, LoginRequest

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.post("/register")
async def register(data: CreateUser):
    """用户注册"""
    # ...

@router.post("/login")
async def login(data: LoginRequest, response: Response):
    """用户登录"""
    # 设置 session cookie

@router.post("/logout")
async def logout():
    """用户登出"""

@router.get("/me")
async def get_current_user():
    """获取当前用户信息"""

@router.get("/favorites")
async def get_favorites():
    """获取用户收藏"""

@router.post("/favorites/{agent_id}")
async def add_favorite(agent_id: str):
    """添加收藏"""

@router.delete("/favorites/{agent_id}")
async def remove_favorite(agent_id: str):
    """移除收藏"""
```

#### 步骤 6: Streamlit UI 集成

```python
# src/ui/pages/auth.py
import streamlit as st

def render_login_page():
    """渲染登录页面"""
    st.title("登录")
    email = st.text_input("邮箱")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        # 调用 API 登录

def render_register_page():
    """渲染注册页面"""
    st.title("注册")
    username = st.text_input("用户名")
    email = st.text_input("邮箱")
    password = st.text_input("密码", type="password")
    if st.button("注册"):
        # 调用 API 注册

def render_account_page():
    """渲染用户账户页面"""
    # 显示收藏、搜索历史、偏好设置
```

### 测试策略

```bash
# 单元测试
pytest tests/test_auth.py -v

# 集成测试
pytest tests/test_auth_api.py -v
```

### 验收标准

- [ ] 用户可以注册/登录
- [ ] 收藏跨会话持久化
- [ ] 搜索历史保存
- [ ] 偏好设置生效
- [ ] 会话安全（token 过期）
- [ ] 密码正确哈希存储

---

## P2: 更多 pSEO 页面模板

### 目标

创建额外的程序化 SEO 页面，提升搜索引擎覆盖率。

### 新增页面类型

#### 1. 设计模式页面 (5 页)

```
/rag-patterns/          # RAG 实现模式
/react-agents/          # ReAct 模式
/tool-use-agents/       # 函数调用模式
/plan-and-execute/      # 规划执行模式
/reflection-agents/     # 自反思模式
```

#### 2. "Best X Agents" 页面 (10 页)

```
/best-rag-agents-2025/
/best-local-llm-agents/
/best-multi-agent-systems/
/best-openai-agents-for-beginners/
/best-free-ai-agents/
/best-langchain-agents/
/best-crewai-agents/
/best-automation-agents/
/best-coding-assistants/
/best-research-assistants/
```

#### 3. 用例落地页 (6 页)

```
/customer-support-agents/    # 客服机器人
/research-assistants/         # 研究助手
/coding-assistants/           # 编程助手
/content-generation/          # 内容生成
/data-analysis/               # 数据分析
/workflow-automation/         # 工作流自动化
```

#### 4. 技术组合页面 (8 页)

```
/langchain-with-openai/
/langchain-with-anthropic/
/crewai-with-local-llms/
/rag-with-pinecone/
/rag-with-chroma/
/multi-agent-with-autogen/
/function-calling-with-gpt4/
/voice-agents-with-whisper/
```

### 文件结构

```
src/export/
├── data.py          # 添加 pSEO 配置
├── templates.py     # 添加新页面模板
└── pages/           # 新增页面模块
    ├── __init__.py
    ├── patterns.py      # 设计模式页面
    ├── best_of.py       # Best X 页面
    ├── use_cases.py     # 用例页面
    └── tech_combos.py   # 技术组合页面
```

### 实施步骤

#### 步骤 1: 扩展 pSEO 配置

```python
# src/export/data.py 新增

# 设计模式配置
DESIGN_PATTERNS = {
    "rag-patterns": {
        "title": "RAG Pattern Agents",
        "description": "Retrieval-Augmented Generation implementation examples",
        "keywords": ["rag", "retrieval", "vector", "embeddings"],
        "related_categories": ["rag", "search"],
    },
    # ... 其他模式
}

# Best X 页面配置
BEST_OF_PAGES = {
    "best-rag-agents-2025": {
        "title": "Best RAG Agents 2025",
        "description": "Top RAG implementation examples for building knowledge-aware AI applications",
        "criteria": lambda a: a.get("category") == "rag",
        "sort_by": "stars",
    },
    # ... 其他页面
}

# 用例配置
USE_CASES = {
    "customer-support-agents": {
        "title": "Customer Support AI Agents",
        "description": "Build intelligent customer service chatbots with these agent examples",
        "frameworks": ["langchain", "crewai"],
        "keywords": ["support", "chatbot", "customer"],
    },
    # ... 其他用例
}
```

#### 步骤 2: 创建页面生成器

```python
# src/export/pages/patterns.py
def generate_pattern_pages(agents: list[dict], output_dir: Path, base_url: str):
    """生成设计模式页面"""
    for slug, config in DESIGN_PATTERNS.items():
        matched_agents = filter_agents(agents, config)
        html = render_pattern_page(slug, config, matched_agents, base_url)
        write(output_dir / f"{slug}/index.html", html)

# src/export/pages/best_of.py
def generate_best_of_pages(agents: list[dict], output_dir: Path, base_url: str):
    """生成 Best X 页面"""
    # 按条件筛选、排序、生成页面

# src/export/pages/use_cases.py
def generate_use_case_pages(agents: list[dict], output_dir: Path, base_url: str):
    """生成用例页面"""
    # 类似实现
```

#### 步骤 3: 更新主导出函数

```python
# src/export/export.py 修改

def export_site(
    data_path: Path,
    output_dir: Path,
    base_url: Optional[str] = None,
) -> None:
    """导出静态网站，包括新的 pSEO 页面"""
    # ... 现有代码

    # 生成设计模式页面
    from src.export.pages.patterns import generate_pattern_pages
    generate_pattern_pages(agents, output_dir, base_url)

    # 生成 Best X 页面
    from src.export.pages.best_of import generate_best_of_pages
    generate_best_of_pages(agents, output_dir, base_url)

    # 生成用例页面
    from src.export.pages.use_cases import generate_use_case_pages
    generate_use_case_pages(agents, output_dir, base_url)
```

### 验收标准

- [ ] 所有新页面生成成功
- [ ] HTML 结构有效
- [ ] Schema.org 标记正确
- [ ] Sitemap 包含新页面
- [ ] 内部链接正确

---

## P3: 移动响应式 CSS 改进

### 目标

优化移动端用户体验，确保所有功能在手机上可用。

### 当前问题

1. CSS 缺少移动端断点
2. 某些元素在小屏幕上溢出
3. 触摸目标太小

### 改进方案

#### 步骤 1: 创建响应式 CSS 模块

```python
# src/ui/styles.py 扩展

RESPONSIVE_CSS = '''
<style>
/* 基础响应式 */
.container {
    max-width: 100%;
    padding: 0 1rem;
    margin: 0 auto;
}

/* 移动端导航 */
@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        transform: translateX(-100%);
        transition: transform 0.3s;
    }
    .sidebar.open {
        transform: translateX(0);
    }
}

/* Agent 卡片网格 */
@media (max-width: 600px) {
    .agent-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
}
@media (min-width: 601px) and (max-width: 900px) {
    .agent-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* 过滤器 */
@media (max-width: 768px) {
    .filters {
        flex-direction: column;
    }
    .filter-group {
        width: 100%;
    }
}

/* 搜索框 */
@media (max-width: 600px) {
    .search-input {
        font-size: 16px; /* 防止 iOS 自动缩放 */
    }
}

/* 按钮 - 最小触摸目标 44x44px */
@media (max-width: 768px) {
    .btn {
        min-height: 44px;
        min-width: 44px;
        padding: 12px 20px;
        font-size: 16px;
    }
}

/* 表格 */
@media (max-width: 768px) {
    table {
        font-size: 14px;
    }
    .table-container {
        overflow-x: auto;
    }
}

/* 模态框/对话框 */
@media (max-width: 600px) {
    .modal {
        width: 95%;
        max-height: 90vh;
    }
}

/* AI 选择器 */
@media (max-width: 768px) {
    .ai-selector {
        flex-direction: column;
    }
    .ai-input {
        width: 100%;
    }
}
</style>
'''
```

#### 步骤 2: 添加移动端导航

```python
# src/ui/components.py 新增

def render_mobile_menu_toggle():
    """渲染移动端菜单切换按钮"""
    st.markdown('''
    <button class="mobile-menu-toggle" aria-label="Toggle menu">
        <span></span>
        <span></span>
        <span></span>
    </button>
    ''', unsafe_allow_html=True)
```

#### 步骤 3: 优化表单输入

```python
# 确保所有输入框在移动端可用
def render_search_input():
    """渲染响应式搜索输入"""
    st.text_input(
        "搜索 agents...",
        key="search_input",
        help="输入关键词搜索",
    )
```

#### 步骤 4: 图片优化

```python
# 响应式图片
RESPONSIVE_IMG_CSS = '''
<style>
img {
    max-width: 100%;
    height: auto;
}
@media (max-width: 600px) {
    .agent-logo {
        width: 48px;
        height: 48px;
    }
}
</style>
'''
```

### 测试策略

```bash
# 在不同设备上测试
# 1. iPhone SE (375x667)
# 2. iPhone 12 Pro (390x844)
# 3. iPad (768x1024)
# 4. Desktop (1920x1080)

# 使用 Chrome DevTools 设备模拟
# 或实际设备测试
```

### 验收标准

- [ ] 所有功能在 iPhone SE 可用
- [ ] 触摸目标 >= 44x44px
- [ ] 无横向滚动（必要情况除外）
- [ ] 文字可读（>= 14px）
- [ ] 图片自适应

---

## 总体时间表

| 任务            | 预计时间 | 依赖 |
| --------------- | -------- | ---- |
| P1: 拆分 api.py | 1-2 天   | 无   |
| P1: 拆分 app.py | 1-2 天   | 无   |
| P2: 用户账户    | 1-2 周   | 无   |
| P2: pSEO 页面   | 3-5 天   | 无   |
| P3: 移动端 CSS  | 2-3 天   | 无   |

**总计**: 约 3-4 周完成所有任务

---

## 执行优先级建议

1. **第 1 周**: P1 任务（拆分 api.py 和 app.py）
   - 立即改善代码可维护性
   - 为后续开发打好基础

2. **第 2 周**: P3 移动端 CSS
   - 快速见效
   - 改善用户体验

3. **第 3-4 周**: P2 pSEO 页面
   - 提升 SEO 流量
   - 可分批交付

4. **第 5-6 周**: P2 用户账户系统
   - 最大工作量
   - 需要仔细设计和测试

---

## 附录：检查清单模板

每个任务完成后，验证：

```markdown
## [任务名称] 完成检查清单

### 代码质量

- [ ] 代码通过 lint 检查 (black, ruff)
- [ ] 类型检查通过 (mypy)
- [ ] 添加了必要的类型注解
- [ ] 添加了文档字符串

### 测试

- [ ] 单元测试覆盖率 >= 80%
- [ ] 集成测试通过
- [ ] 手动测试通过
- [ ] 无回归问题

### 兼容性

- [ ] 向后兼容导入有效
- [ ] API 端点响应正常
- [ ] Streamlit 应用正常启动
- [ ] 现有功能无破坏

### 文档

- [ ] 更新 CLAUDE.md
- [ ] 更新 README.md（如需要）
- [ ] 添加/更新测试文件
- [ ] 代码注释充分

### 部署

- [ ] 环境变量配置正确
- [ ] 数据库迁移脚本（如需要）
- [ ] 新文件已添加到版本控制
```
