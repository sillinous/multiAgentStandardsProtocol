use clap::Parser;
use tracing_subscriber::{fmt, EnvFilter};

#[derive(Parser, Debug)]
#[command(name = "agentic-cli", version, about = "Agentic ecosystem CLI")]
struct Args {
    #[command(subcommand)]
    command: Command,
}

#[derive(Parser, Debug)]
enum Command {
    /// Create a standardized agent from a template
    Scaffold {
        /// Template ID (e.g., tmpl.standard.worker)
        #[arg(long)]
        template: String,

        /// Agent name
        #[arg(long)]
        name: String,

        /// Agent description
        #[arg(long, default_value = "")] 
        desc: String,
    },
    /// List available templates
    TemplatesList,
    /// Show a template summary
    TemplatesShow {
        /// Template ID
        #[arg(long)]
        template: String,
    },
    /// List registered agents (in-memory, per run)
    AgentsList,
}

fn main() {
    // minimal tracing init
    let _ = fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .try_init();

    let args = Args::parse();
    // ephemeral in-memory registry for the process
    static mut REGISTRY: Option<agentic_factory::AgentRegistry> = None;
    unsafe {
        if REGISTRY.is_none() { REGISTRY = Some(agentic_factory::AgentRegistry::new()); }
    }
    match args.command {
        Command::Scaffold { template, name, desc } => {
            // Also register in the ephemeral registry
            let id_res = unsafe { agentic_cli::create_and_register(&template, &name, &desc, REGISTRY.as_mut().unwrap()) };
            if let Err(err) = id_res {
                eprintln!("Error: {}", err);
                std::process::exit(1);
            }
            let _ = agentic_cli::scaffold_standardized_agent(&template, &name, &desc);
        }
        Command::TemplatesList => {
            let items = agentic_cli::list_templates();
            if items.is_empty() {
                println!("No templates available");
            } else {
                for (id, name) in items { println!("{} - {}", id, name); }
            }
        }
        Command::TemplatesShow { template } => {
            match agentic_cli::show_template(&template) {
                Some(s) => println!("{}: {}", template, s),
                None => println!("Template not found: {}", template),
            }
        }
        Command::AgentsList => {
            let lines = unsafe { agentic_cli::list_registered(REGISTRY.as_ref().unwrap()) };
            if lines.is_empty() { println!("No agents registered yet"); } else { for l in lines { println!("{}", l); } }
        }
    }
}


