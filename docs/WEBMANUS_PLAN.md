# WebManus.com 产品规划

> Manus = 拉丁语"手" = 劳动力 → AI 数字员工评测导航站

## 定位转型

| 现有 Agent Navigator            | WebManus.com                            |
| ------------------------------- | --------------------------------------- |
| 索引代码示例 (awesome-llm-apps) | AI Agent **产品**评测导航               |
| 面向开发者                      | 面向普通用户 + 开发者                   |
| 按框架分类 (LangChain, CrewAI)  | 按**使用场景**分类                      |
| 静态展示                        | 评测 + 对比 + UGC 评价                  |
| 单一数据源                      | 多源聚合 (Product Hunt, 独立产品, 大厂) |

## 核心功能

### 1. Agent 目录 (保留/改造)

```
场景分类:
├── 写作助手 (Writing)
├── 编程助手 (Coding)
├── 数据分析 (Data)
├── 自动化办公 (Automation)
├── 客服/销售 (Customer Service)
├── 研究/搜索 (Research)
├── 创意/设计 (Creative)
├── 个人助理 (Personal)
└── 企业级 (Enterprise)
```

### 2. 智能推荐 (改造现有 AI Selector)

- 用户输入: "我想让 AI 帮我每天整理邮件并自动回复"
- 输出: 推荐 3-5 个最匹配的 Agent，带理由

### 3. 对比评测 (新增)

- `/manus-vs-devin` → 自动生成对比页
- 维度: 能力、价格、易用性、速度、准确性
- pSEO 机会: `[A]-vs-[B]` 页面批量生成

### 4. 评分体系 (新增)

```
综合评分 =
  能力 (40%) + 易用性 (25%) + 性价比 (20%) + 稳定性 (15%)

单项评分:
- 任务完成率
- 响应速度
- 价格/token
- 学习曲线
- API 可用性
```

### 5. 趋势追踪 (新增)

- 本周新发布
- 热度上升榜
- 讨论度 (Twitter/Reddit 提及)
- 融资/估值追踪

### 6. 用户评价 (新增)

- 星级评分
- 使用场景标签
- "真实用了 X 个月" 徽章
- 投票: 有帮助 / 无帮助

## 数据模型改造

```python
# 现有 agent schema
{
    "id": "xxx",
    "category": "rag",           # 太开发者向
    "frameworks": ["langchain"], # 产品不需要这个
    ...
}

# WebManus schema
{
    "id": "manus-ai",
    "name": "Manus",
    "tagline": "通用 AI Agent，能操作浏览器完成复杂任务",

    # 场景分类 (多选)
    "use_cases": ["automation", "research", "data"],

    # 产品信息
    "pricing": {
        "model": "freemium",  # free, freemium, paid, enterprise
        "free_tier": "10 tasks/month",
        "paid_starts": "$39/month"
    },
    "company": "Manus AI",
    "founded": "2024",
    "funding": "$25M Series A",

    # 评测数据
    "scores": {
        "overall": 8.5,
        "capability": 9.0,
        "usability": 8.0,
        "value": 7.5,
        "reliability": 8.5
    },

    # 技术细节 (给开发者看)
    "tech": {
        "api_available": true,
        "open_source": false,
        "base_model": "Claude + GPT-4",
        "browser_control": true
    },

    # SEO/展示
    "logo_url": "...",
    "screenshots": [...],
    "video_demo": "...",

    # 趋势
    "metrics": {
        "monthly_visits": 500000,
        "twitter_mentions_7d": 1200,
        "product_hunt_rank": 3
    }
}
```

## pSEO 页面矩阵

| 页面模式                     | 示例                       | 预估搜索量 |
| ---------------------------- | -------------------------- | ---------- |
| `/best-ai-agent-for-[task]`  | best-ai-agent-for-coding   | 高         |
| `/[agent]-review`            | manus-review               | 中         |
| `/[agent]-vs-[agent]`        | manus-vs-devin             | 中         |
| `/[agent]-alternatives`      | manus-alternatives         | 中         |
| `/[agent]-pricing`           | manus-pricing              | 中         |
| `/free-ai-agents-for-[task]` | free-ai-agents-for-writing | 高         |

## 数据采集策略

### 自动采集

1. Product Hunt API → 新产品
2. Twitter/X 搜索 → 热度/讨论
3. SimilarWeb/Semrush API → 流量估算
4. GitHub → 开源项目 stars

### 人工补充

1. 编辑评测 (每周 2-3 篇深度评测)
2. 用户提交 (Submit Agent 表单)
3. 合作方数据

## 技术改造优先级

### Phase 1: MVP (1-2 周)

- [ ] 数据模型改造 (新 schema)
- [ ] 首批 50 个热门 Agent 数据录入
- [ ] 分类改为用户场景
- [ ] 基础搜索/筛选

### Phase 2: 评测体系 (2-3 周)

- [ ] 评分系统
- [ ] 对比页面生成器
- [ ] pSEO 模板页

### Phase 3: UGC (3-4 周)

- [ ] 用户注册/登录
- [ ] 评价系统
- [ ] 投票/排序

### Phase 4: 数据自动化 (持续)

- [ ] Product Hunt 集成
- [ ] Twitter 热度追踪
- [ ] 自动更新 pipeline

## 竞品参考

| 竞品                   | 定位         | 可借鉴             |
| ---------------------- | ------------ | ------------------ |
| There's An AI For That | AI 工具导航  | 分类体系、提交流程 |
| G2.com                 | 企业软件评测 | 评分体系、对比页   |
| Product Hunt           | 新产品发现   | 热度机制、UGC      |
| AlternativeTo          | 替代品推荐   | 关联推荐           |

## 域名优势

`WebManus.com` 暗示:

- Web 上的"手" = 帮你在网上干活的 AI
- 与 Manus AI 热点关联 (但不侵权)
- 朗朗上口，易记

---

**下一步**: 确认方向后，开始 Phase 1 改造
