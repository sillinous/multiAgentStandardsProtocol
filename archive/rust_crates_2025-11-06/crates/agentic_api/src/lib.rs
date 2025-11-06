//! Minimal Axum API server: templates, agents, and a simple HTML UI

use axum::{routing::{get, post, delete}, Router, extract::Path, Json, response::Html};
use serde::{Deserialize, Serialize};
use tracing::instrument;
use std::sync::{Arc, Mutex};
use agentic_factory::{AgentFactory, AgentRegistry};
use agentic_standards::{StandardsAgent};
use agentic_protocols::{MockMcpAdapter, MockA2aAdapter};
use agentic_runtime::{
    executor::{AgentExecutor, DefaultExecutor, ExecutionResult},
    context::ExecutionContext,
    scheduler::{TaskScheduler, Task, TaskPriority, TaskStatus},
    llm::{MockLlmClient, LlmClient},
};
use std::fs;
use std::path::PathBuf;
use std::collections::HashMap;

mod execution;
use execution::*;

mod business;
use business::BusinessState;

mod dashboard_ws;
pub use dashboard_ws::{DashboardState, DashboardEvent, broadcast_event};

#[derive(Clone)]
pub struct AppState {
    pub standards: StandardsAgent,
    pub factory: AgentFactory,
    pub registry: Arc<Mutex<AgentRegistry>>,
    pub storage: Arc<Mutex<PersistedStore>>,
    pub messages: Arc<Mutex<HashMap<String, Vec<AgentMessage>>>>,
    pub workflows: Arc<Mutex<HashMap<String, Workflow>>>,
    pub executor: Arc<DefaultExecutor>,
    pub scheduler: Arc<TaskScheduler>,
    pub learning_engine: Arc<Mutex<agentic_learning::LearningEngine>>,
    pub business_state: Arc<BusinessState>,
    pub dashboard_state: DashboardState,
}

impl AppState {
    pub fn new() -> Self {
        let standards = StandardsAgent::new();
        let factory = AgentFactory::from_registry(standards.registry().clone());
        let registry = Arc::new(Mutex::new(AgentRegistry::new()));
        let storage = Arc::new(Mutex::new(PersistedStore::load_default()));
        let messages = Arc::new(Mutex::new(HashMap::new()));
        let workflows = Arc::new(Mutex::new(HashMap::new()));

        // Create executor with mock LLM (can be configured with real LLM via env)
        let llm_client: Arc<dyn LlmClient> = Arc::new(MockLlmClient::default());
        let executor = Arc::new(DefaultExecutor::new(llm_client));

        // Create task scheduler
        let scheduler = Arc::new(TaskScheduler::new());

        // Create learning engine
        let learning_engine = Arc::new(Mutex::new(agentic_learning::LearningEngine::new()));

        // Create dashboard state
        let dashboard_state = DashboardState::new();

        // Create business state (with dashboard state for event broadcasting)
        let business_state = Arc::new(BusinessState::new(llm_client.clone(), dashboard_state.clone()));

        Self {
            standards,
            factory,
            registry,
            storage,
            messages,
            workflows,
            executor,
            scheduler,
            learning_engine,
            business_state,
            dashboard_state,
        }
    }
}

#[derive(Deserialize)]
pub struct CreateAgentReq {
    pub template_id: String,
    pub name: String,
    pub description: String,
}

#[derive(Serialize)]
pub struct CreateAgentRes { pub id: String }

pub fn router(state: AppState) -> Router {
    // Create business routes with dedicated state
    let business_routes = business::create_business_routes(state.business_state.clone());

    // Create dashboard routes with dedicated state
    let dashboard_routes = dashboard_ws::create_dashboard_routes(state.dashboard_state.clone());

    Router::new()
        .route("/", get(ui_index))
        .route("/dashboard", get(ui_dashboard))
        .route("/api/health", get(api_health))
        .route("/api/version", get(api_version))
        .route("/api/templates", get(api_templates))
        .route("/api/templates/:id", get(api_template_show))
        .route("/api/agents", get(api_agents).post(api_agents_create))
        .route("/api/agents/:id/compliance", get(api_agent_compliance))
        .route("/api/agents/:id", delete(api_agents_delete))
        .route("/api/agents/:id/detail", get(api_agent_detail))
        .route("/api/agents/:id/messages", get(api_agent_messages).post(api_agent_send_message))
        .route("/api/protocols/mcp/:id/tools", get(api_mcp_tools))
        .route("/api/protocols/mcp/:id/invoke", post(api_mcp_invoke))
        .route("/api/protocols/a2a/send", post(api_a2a_send))
        .route("/api/workflows", get(api_workflows_list).post(api_workflows_create))
        .route("/api/workflows/:id", get(api_workflows_get))
        .route("/api/agents/:id/execute", post(api_agent_execute))
        .route("/api/tasks", get(api_tasks_list).post(api_tasks_create))
        .route("/api/tasks/:id", get(api_task_get))
        .route("/api/tasks/:id/status", get(api_task_status))
        .route("/api/learning/stats", get(api_learning_stats))
        .route("/api/learning/events/:agent_id", get(api_learning_events))
        .with_state(state)
        // Merge business routes under /api/
        .merge(Router::new().nest("/api", business_routes))
        // Merge dashboard routes under /api/dashboard/
        .merge(Router::new().nest("/api/dashboard", dashboard_routes))
}

async fn ui_dashboard() -> Html<String> {
    let dashboard_html = include_str!("../dashboard.html");
    Html(dashboard_html.to_string())
}

async fn ui_index() -> Html<String> {
    let html = r#"<!doctype html>
<html>
<head><meta charset=\"utf-8\"><title>Agentic Ecosystem</title></head>
<body>
  <h1>Agentic Ecosystem</h1>
  <nav>
    <button id=\"tab-agents\">Agents</button>
    <button id=\"tab-protocols\">Protocols</button>
    <button id=\"tab-workflows\">Workflows</button>
  </nav>
  <section>
    <h2>Templates</h2>
    <div id=\"templates\"></div>
  </section>
  <section id=\"sec-agents\">
    <h2>Create Agent</h2>
    <form id=\"create\">
      <input name=\"template_id\" placeholder=\"tmpl.standard.worker\" value=\"tmpl.standard.worker\"/>
      <input name=\"name\" placeholder=\"Name\" value=\"StdWorker1\"/>
      <input name=\"description\" placeholder=\"Description\" value=\"Standard worker\"/>
      <button type=\"submit\">Create</button>
    </form>
  </section>
  <section id=\"sec-protocols\" style=\"display:none\">
    <h2>Agents</h2>
    <div id=\"agents\"></div>
  </section>
  <section id=\"sec-workflows\" style=\"display:none\">
    <h2>Workflows</h2>
    <form id=\"wf-create\">
      Supervisor Name <input name=\"supervisor\" placeholder=\"Supervisor\" value=\"Supervisor\"/>
      Workers <input name=\"n\" type=\"number\" value=\"2\"/> Template <input name=\"template_id\" value=\"tmpl.standard.worker\"/>
      <button type=\"submit\">Create Workflow</button>
    </form>
    <div id=\"workflows\"></div>
  </section>
  <section>
    <h2>Protocols</h2>
    <div>
      <b>MCP</b>: Agent ID <input id=\"mcp-id\" placeholder=\"agent id\"/> 
      <button id=\"mcp-list\">List Tools</button>
      <div>Tool: <input id=\"mcp-tool\" placeholder=\"echo\"/> Input: <input id=\"mcp-input\" placeholder=\"hello\"/> <button id=\"mcp-invoke\">Invoke</button></div>
      <pre id=\"mcp-out\"></pre>
    </div>
    <div style=\"margin-top:8px\">
      <b>A2A</b>: From <input id=\"a2a-from\" placeholder=\"from id\"/> To <input id=\"a2a-to\" placeholder=\"to id\"/> Content <input id=\"a2a-content\" placeholder=\"hi\"/> <button id=\"a2a-send\">Send</button>
      <pre id=\"a2a-out\"></pre>
    </div>
  </section>
  <script>
    function showTab(which){
      document.getElementById('sec-agents').style.display = which==='agents'?'block':'none';
      document.getElementById('sec-protocols').style.display = which==='protocols'?'block':'none';
      document.getElementById('sec-workflows').style.display = which==='workflows'?'block':'none';
    }
    document.getElementById('tab-agents').addEventListener('click', ()=>showTab('agents'));
    document.getElementById('tab-protocols').addEventListener('click', ()=>showTab('protocols'));
    document.getElementById('tab-workflows').addEventListener('click', ()=>showTab('workflows'));
    async function loadTemplates(){
      const r = await fetch('/api/templates');
      const data = await r.json();
      document.getElementById('templates').innerText = JSON.stringify(data, null, 2);
    }
    async function loadAgents(){
      const r = await fetch('/api/agents');
      const data = await r.json();
      const container = document.getElementById('agents');
      container.innerHTML = '';
      for (const a of data) {
        const div = document.createElement('div');
        div.style.marginBottom = '12px';
        div.innerHTML = `<b>${a[1]}</b> <code>${a[0]}</code>
          <button data-id="${a[0]}" class="show">Compliance</button>
          <button data-id="${a[0]}" class="del">Delete</button>
          <button data-id="${a[0]}" class="detail">Details</button>
          <div style="margin-top:6px">Message: <input id="m-${a[0]}" placeholder="Hello"/> <button data-id="${a[0]}" class="send">Send</button></div>
          <pre id="c-${a[0]}"></pre>
          <pre id="d-${a[0]}"></pre>
          <pre id="h-${a[0]}"></pre>`;
        container.appendChild(div);
      }
      container.querySelectorAll('.show').forEach(btn=>{
        btn.addEventListener('click', async ()=>{
          const id = btn.getAttribute('data-id');
          const r = await fetch(`/api/agents/${id}/compliance`);
          const comp = await r.json();
          document.getElementById(`c-${id}`).textContent = JSON.stringify(comp, null, 2);
          const h = await fetch(`/api/agents/${id}/messages`);
          const hist = await h.json();
          document.getElementById(`h-${id}`).textContent = JSON.stringify(hist, null, 2);
        });
      });
      container.querySelectorAll('.del').forEach(btn=>{
        btn.addEventListener('click', async ()=>{
          const id = btn.getAttribute('data-id');
          await fetch(`/api/agents/${id}`, { method:'DELETE' });
          await loadAgents();
        });
      });
      container.querySelectorAll('.detail').forEach(btn=>{
        btn.addEventListener('click', async ()=>{
          const id = btn.getAttribute('data-id');
          const r = await fetch(`/api/agents/${id}/detail`);
          const det = await r.json();
          document.getElementById(`d-${id}`).textContent = JSON.stringify(det, null, 2);
        });
      });
      container.querySelectorAll('.send').forEach(btn=>{
        btn.addEventListener('click', async ()=>{
          const id = btn.getAttribute('data-id');
          const msg = document.getElementById(`m-${id}`).value;
          await fetch(`/api/agents/${id}/messages`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ content: msg }) });
          const h = await fetch(`/api/agents/${id}/messages`);
          const hist = await h.json();
          document.getElementById(`h-${id}`).textContent = JSON.stringify(hist, null, 2);
        });
      });
    }
    document.getElementById('create').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = Object.fromEntries(fd.entries());
      await fetch('/api/agents', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
      await loadAgents();
    });
    document.getElementById('mcp-list').addEventListener('click', async ()=>{
      const id = document.getElementById('mcp-id').value;
      const r = await fetch(`/api/protocols/mcp/${id}/tools`);
      document.getElementById('mcp-out').textContent = JSON.stringify(await r.json(), null, 2);
    });
    document.getElementById('mcp-invoke').addEventListener('click', async ()=>{
      const id = document.getElementById('mcp-id').value;
      const tool = document.getElementById('mcp-tool').value;
      const input = document.getElementById('mcp-input').value;
      const r = await fetch(`/api/protocols/mcp/${id}/invoke`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ tool, input })});
      document.getElementById('mcp-out').textContent = JSON.stringify(await r.json(), null, 2);
    });
    document.getElementById('a2a-send').addEventListener('click', async ()=>{
      const from = document.getElementById('a2a-from').value;
      const to = document.getElementById('a2a-to').value;
      const content = document.getElementById('a2a-content').value;
      const r = await fetch(`/api/protocols/a2a/send`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ from, to, content })});
      document.getElementById('a2a-out').textContent = JSON.stringify(await r.json(), null, 2);
    });
    async function loadWorkflows(){
      const r = await fetch('/api/workflows');
      document.getElementById('workflows').textContent = JSON.stringify(await r.json(), null, 2);
    }
    document.getElementById('wf-create').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = Object.fromEntries(fd.entries());
      body.n = parseInt(body.n, 10) || 1;
      await fetch('/api/workflows', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
      await loadWorkflows();
    });
    loadTemplates(); loadAgents();
    loadWorkflows();
  </script>
 </body>
</html>"#;
    Html(html.to_string())
}

async fn api_templates(axum::extract::State(state): axum::extract::State<AppState>) -> Json<Vec<(String, String)>> {
    // MVP: only known template
    let id = "tmpl.standard.worker".to_string();
    let name = state
        .standards
        .registry()
        .get_template(&id)
        .map(|t| t.display_name.clone())
        .unwrap_or_else(|| "Unknown".into());
    Json(vec![(id, name)])
}

async fn api_template_show(
    axum::extract::State(state): axum::extract::State<AppState>,
    Path(id): Path<String>,
) -> Json<Option<String>> {
    let s = state
        .standards
        .registry()
        .get_template(&id)
        .map(|t| format!("{} - {}", t.display_name, t.description));
    Json(s)
}

#[instrument(skip(state))]
#[instrument(skip(state))]
async fn api_agents(axum::extract::State(state): axum::extract::State<AppState>) -> Json<Vec<(String, String)>> {
    let reg = state.registry.lock().unwrap();
    let list: Vec<(String,String)> = reg.list_agents().into_iter().map(|a| (a.id.to_string(), a.name.clone())).collect();
    drop(reg);
    if list.is_empty() {
        let store = state.storage.lock().unwrap();
        let fallback: Vec<(String,String)> = store.list().into_iter().map(|x| (x.id, x.name)).collect();
        return Json(fallback);
    }
    Json(list)
}

#[instrument(skip(state, req))]
#[instrument(skip(state, req))]
async fn api_agents_create(
    axum::extract::State(state): axum::extract::State<AppState>,
    Json(req): Json<CreateAgentReq>,
) -> Json<CreateAgentRes> {
    let (agent, genome) = state
        .factory
        .create_from_template(&req.template_id, &req.name, &req.description)
        .expect("create");
    let id = agent.id.to_string();
    state.registry.lock().unwrap().register(agent, genome);
    // persist lightweight record
    state.storage.lock().unwrap().add(StoredAgent { id: id.clone(), template_id: req.template_id, name: req.name, description: req.description });
    Json(CreateAgentRes { id })
}

#[derive(Serialize, Deserialize, Clone)]
struct StoredAgent { id: String, template_id: String, name: String, description: String }

#[derive(Default)]
pub struct PersistedStore { path: PathBuf, items: Vec<StoredAgent> }

#[derive(Serialize, Deserialize, Default)]
struct PersistedData {
    agents: Vec<StoredAgent>,
    workflows: Vec<Workflow>,
}

impl PersistedStore {
    pub fn load_default() -> Self {
        let path = Self::default_path();
        if let Ok(bytes) = fs::read(&path) {
            // try new format
            if let Ok(pd) = serde_json::from_slice::<PersistedData>(&bytes) {
                return Self { path, items: pd.agents };
            }
            // fallback old format (agents array)
            if let Ok(items) = serde_json::from_slice::<Vec<StoredAgent>>(&bytes) {
                return Self { path, items };
            }
        }
        Self { path, items: vec![] }
    }

    fn default_path() -> PathBuf {
        let mut p = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        p.push(".agentic_store.json");
        p
    }

    pub fn add(&mut self, item: StoredAgent) { self.items.push(item); let _ = self.save(); }
    pub fn remove(&mut self, id: &str) { self.items.retain(|x| x.id != id); let _ = self.save(); }
    pub fn get(&self, id: &str) -> Option<StoredAgent> { self.items.iter().find(|x| x.id == id).cloned() }
    pub fn list(&self) -> Vec<StoredAgent> { self.items.clone() }

    pub fn add_workflow(&mut self, wf: Workflow) { let mut data = self.read_all(); data.workflows.push(wf); let _ = self.write_all(&data); }
    pub fn list_workflows(&self) -> Vec<Workflow> { self.read_all().workflows }

    fn save(&self) -> std::io::Result<()> {
        let mut data = self.read_all();
        data.agents = self.items.clone();
        self.write_all(&data)
    }

    fn read_all(&self) -> PersistedData {
        if let Ok(bytes) = fs::read(&self.path) {
            if let Ok(pd) = serde_json::from_slice::<PersistedData>(&bytes) { return pd; }
        }
        PersistedData::default()
    }

    fn write_all(&self, data: &PersistedData) -> std::io::Result<()> {
        let bytes = serde_json::to_vec_pretty(data).unwrap_or_default();
        fs::write(&self.path, bytes)
    }
}

#[instrument(skip(state))]
#[instrument(skip(state))]
async fn api_agent_compliance(
    axum::extract::State(state): axum::extract::State<AppState>,
    Path(id): Path<String>,
) -> Json<Option<serde_json::Value>> {
    let store = state.storage.lock().unwrap();
    if let Some(sa) = store.get(&id) {
        let reg = state.registry.lock().unwrap();
        if let Some(agent) = reg.get_agent(&id) {
            if let Some(report) = state.standards.compliance_for_template(&sa.template_id, agent) {
                return Json(Some(serde_json::json!({
                    "standard": report.standard.0,
                    "compliant": report.compliant,
                    "missing_protocols": report.missing_protocols,
                    "missing_capabilities": report.missing_capabilities,
                    "notes": report.notes,
                })));
            }
        }
    }
    Json(None)
}

#[instrument(skip(state))]
#[instrument(skip(state))]
async fn api_agents_delete(
    axum::extract::State(state): axum::extract::State<AppState>,
    Path(id): Path<String>,
) -> Json<bool> {
    // Remove from registry and persistence
    state.registry.lock().unwrap().remove(&id);
    state.storage.lock().unwrap().remove(&id);
    state.messages.lock().unwrap().remove(&id);
    Json(true)
}

async fn api_health() -> Json<serde_json::Value> {
    Json(serde_json::json!({"status":"ok"}))
}

async fn api_version() -> Json<serde_json::Value> {
    Json(serde_json::json!({"version":"0.1.0-alpha"}))
}

#[instrument(skip(state))]
#[instrument(skip(state))]
async fn api_agent_detail(
    axum::extract::State(state): axum::extract::State<AppState>,
    Path(id): Path<String>,
) -> Json<Option<serde_json::Value>> {
    let reg = state.registry.lock().unwrap();
    if let Some(agent) = reg.get_agent(&id) {
        let cfg: Vec<(String, String)> = agent.config.iter().map(|(k,v)| (k.clone(), v.clone())).collect();
        return Json(Some(serde_json::json!({
            "id": agent.id.to_string(),
            "name": agent.name,
            "description": agent.description,
            "role": agent.role.to_string(),
            "model": agent.model,
            "provider": agent.provider,
            "tags": agent.tags,
            "version": agent.version,
            "config": cfg,
        })));
    }
    Json(None)
}

#[derive(Serialize, Deserialize, Clone)]
struct AgentMessage { ts: String, from: String, to: String, content: String }

#[derive(Deserialize)]
struct SendMessageReq { content: String }

#[instrument(skip(state))]
async fn api_agent_messages(
    axum::extract::State(state): axum::extract::State<AppState>,
    Path(id): Path<String>,
) -> Json<Vec<AgentMessage>> {
    let map = state.messages.lock().unwrap();
    let v = map.get(&id).cloned().unwrap_or_default();
    Json(v)
}

#[instrument(skip(state, req))]
async fn api_agent_send_message(
    axum::extract::State(state): axum::extract::State<AppState>,
    Path(id): Path<String>,
    Json(req): Json<SendMessageReq>,
) -> Json<bool> {
    let now = chrono::Utc::now().to_rfc3339();
    let mut map = state.messages.lock().unwrap();
    let entry = map.entry(id.clone()).or_insert_with(Vec::new);
    entry.push(AgentMessage { ts: now.clone(), from: "user".into(), to: id.clone(), content: req.content.clone() });
    // Mock agent response: uppercase echo
    entry.push(AgentMessage { ts: now, from: id.clone(), to: "user".into(), content: format!("{}", req.content.to_uppercase()) });
    Json(true)
}

#[derive(Serialize)]
struct McpInvokeRes { tool: String, input: String, output: String }

#[derive(Deserialize)]
struct McpInvokeReq { tool: String, input: String }

#[instrument]
async fn api_mcp_tools(
    Path(_id): Path<String>,
) -> Json<Vec<agentic_protocols::McpTool>> {
    let mcp = MockMcpAdapter;
    Json(mcp.list_tools())
}

#[instrument]
async fn api_mcp_invoke(
    Path(_id): Path<String>,
    Json(req): Json<McpInvokeReq>,
) -> Json<McpInvokeRes> {
    let mcp = MockMcpAdapter;
    let out = mcp.invoke(&req.tool, &req.input);
    Json(McpInvokeRes { tool: req.tool, input: req.input, output: out })
}

#[derive(Serialize, Deserialize)]
struct A2aSendReq { from: String, to: String, content: String }

#[instrument]
async fn api_a2a_send(
    Json(req): Json<A2aSendReq>,
) -> Json<agentic_protocols::A2aEnvelope> {
    let a2a = MockA2aAdapter;
    Json(a2a.envelope(&req.from, &req.to, &req.content))
}

#[derive(Serialize, Deserialize, Clone)]
struct Workflow {
    id: String,
    supervisor_id: String,
    worker_ids: Vec<String>,
}

#[derive(Deserialize)]
struct WorkflowCreateReq { supervisor: String, n: usize, template_id: String }

#[derive(Serialize)]
struct WorkflowCreateRes { id: String, supervisor_id: String, worker_ids: Vec<String> }

#[instrument(skip(state, req))]
async fn api_workflows_create(
    axum::extract::State(state): axum::extract::State<AppState>,
    Json(req): Json<WorkflowCreateReq>,
) -> Json<WorkflowCreateRes> {
    // create supervisor
    let sup_name = req.supervisor;
    let (mut sup_agent, sup_genome) = state.factory.create_from_template(&req.template_id, &sup_name, "Supervisor agent").unwrap();
    sup_agent.set_status(agentic_core::agent::AgentStatus::Running);
    let sup_id = sup_agent.id.to_string();
    state.registry.lock().unwrap().register(sup_agent, sup_genome);

    // create workers
    let mut workers = Vec::new();
    for i in 0..req.n.max(1) {
        let name = format!("Worker-{}", i + 1);
        let (mut w_agent, w_genome) = state.factory.create_from_template(&req.template_id, &name, "Worker agent").unwrap();
        w_agent.set_status(agentic_core::agent::AgentStatus::Running);
        let wid = w_agent.id.to_string();
        state.registry.lock().unwrap().register(w_agent, w_genome);
        workers.push(wid);
    }

    let wf_id = format!("wf-{}", chrono::Utc::now().timestamp_millis());
    state.workflows.lock().unwrap().insert(wf_id.clone(), Workflow { id: wf_id.clone(), supervisor_id: sup_id.clone(), worker_ids: workers.clone() });
    state.storage.lock().unwrap().add_workflow(Workflow { id: wf_id.clone(), supervisor_id: sup_id.clone(), worker_ids: workers.clone() });
    Json(WorkflowCreateRes { id: wf_id, supervisor_id: sup_id, worker_ids: workers })
}

#[instrument(skip(state))]
async fn api_workflows_list(
    axum::extract::State(state): axum::extract::State<AppState>,
) -> Json<Vec<Workflow>> {
    let mem: Vec<Workflow> = state.workflows.lock().unwrap().values().cloned().collect();
    if mem.is_empty() {
        let persisted = state.storage.lock().unwrap().list_workflows();
        return Json(persisted);
    }
    Json(mem)
}

#[instrument(skip(state))]
async fn api_workflows_get(
    axum::extract::State(state): axum::extract::State<AppState>,
    Path(id): Path<String>,
) -> Json<Option<Workflow>> {
    let wf = state.workflows.lock().unwrap().get(&id).cloned();
    Json(wf)
}
