# 🔭 MRAG: Architectural Vision & Roadmap

## The Core Philosophy
**MRAG (Mini Foundry RAG)** is designed as a **production-grade kernel** for enterprise AI retrieval systems. Unlike academic demos, MRAG prioritizes **security**, **observability**, and **operational resilience** over feature bloat.

We follow the **"Polished Core"** doctrine: Do fewer things, but do them with production quality.

## 🏗️ Architectural Blueprint (Current State)

```mermaid
graph TD
    Client[Client / UI / API Consumer] -->|HTTPS + API Key| Gateway[FastAPI Gateway]
    Gateway -->|Rate Limit Check| Limiter[Rate Limiter (In-Memory)]
    
    subgraph "Secure Core"
        Gateway -->|Managed Identity| KV[Azure Key Vault]
        Gateway -->|Logs & Metrics| Insights[Azure App Insights]
    end
    
    subgraph "Intelligence Pipeline"
        Gateway -->|1. Retrieve| Search[Search Service (Mock/Azure AI Search)]
        Search -->|Context| Gateway
        Gateway -->|2. Guardrail Check| Policy[Policy Engine]
        Policy -->|If Valid| LLM[LLM Service (Gemini)]
    end
    
    LLM -->|Answer + Usage Data| Gateway
🗺️ Future Roadmap (From Kernel to Platform)
1. From Single-Tenant to Multi-Tenant (RBAC)
Current: Simple API Key mechanism linked to kb_id.
Vision: Implement OAuth2 with Azure AD. Assign distinct kb_id access per tenant policy, allowing true data isolation for multiple clients.
2. From Keyword Match to Cognitive Retrieval
Current: In-memory keyword matching (Mock).
Vision: Integrate Azure AI Search with Hybrid Search (Vector + Keyword) + Semantic Reranking (L2/Cosine) for higher precision in Arabic content.
3. From Static Policy to Dynamic Governance
Current: Hardcoded thresholds (Score > 0).
Vision: Externalize policy to a rules engine (e.g., OPA - Open Policy Agent) to allow admins to adjust strictness without redeploying code.
4. Infrastructure Evolution
Current: Docker on Azure App Service (PaaS).
Vision: Migration to AKS (Kubernetes) for high-density scaling and event-driven processing (KEDA) for heavy ingestion workloads.

