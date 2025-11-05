//! CLI helpers (library side) for scaffolding standardized agents

use agentic_core::Result;
use agentic_factory::{AgentFactory, AgentRegistry};
use agentic_standards::{StandardsAgent, StandardsRegistry};

pub fn scaffold_standardized_agent(template_id: &str, name: &str, description: &str) -> Result<()> {
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());

    let (agent, _genome) = factory.create_from_template(template_id, name, description)?;

    if let Some(report) = standards_agent.compliance_for_template(template_id, &agent) {
        println!("Compliance for {}: {}", template_id, report.compliant);
        if !report.compliant {
            println!("Missing protocols: {:?}", report.missing_protocols);
            println!("Missing capabilities: {:?}", report.missing_capabilities);
        }
    }

    println!("Created agent '{}' with id {}", agent.name, agent.id);
    Ok(())
}

pub fn list_templates() -> Vec<(String, String)> {
    let sa = StandardsAgent::new();
    let reg: &StandardsRegistry = sa.registry();
    // MVP: we don't have iteration API; list known ids
    let known = vec!["tmpl.standard.worker".to_string()];
    known
        .into_iter()
        .filter_map(|id| reg.get_template(&id).map(|t| (id, t.display_name.clone())))
        .collect()
}

pub fn show_template(template_id: &str) -> Option<String> {
    let sa = StandardsAgent::new();
    sa.registry()
        .get_template(template_id)
        .map(|t| format!("{} - {}", t.display_name, t.description))
}

pub fn create_and_register(template_id: &str, name: &str, description: &str, registry: &mut AgentRegistry) -> Result<String> {
    let standards_agent = StandardsAgent::new();
    let factory = AgentFactory::from_registry(standards_agent.registry().clone());
    let (agent, genome) = factory.create_from_template(template_id, name, description)?;
    let id = agent.id.to_string();
    registry.register(agent, genome);
    Ok(id)
}

pub fn list_registered(registry: &AgentRegistry) -> Vec<String> {
    registry
        .list_agents()
        .into_iter()
        .map(|a| format!("{} [{}]", a.name, a.id))
        .collect()
}
