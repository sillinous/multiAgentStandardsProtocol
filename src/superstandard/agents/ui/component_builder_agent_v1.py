"""
Component Builder Agent v1
Specialized agent for building React/Next.js components with TypeScript
"""

from typing import Dict, List, Any
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from agents.base_agent import BaseAgent, AgentCapability, MessageType


class ComponentBuilderAgent(BaseAgent):
    """
    Specialized agent for building React/Next.js components

    Capabilities:
    - React component development with TypeScript
    - Tailwind CSS styling
    - Framer Motion animations
    - Component architecture and best practices
    - Props interfaces and type safety
    """

    def __init__(
        self, agent_id: str = "component_builder_001", workspace_path: str = "./workspace"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="component_builder",
            capabilities=[
                AgentCapability.DEVELOPMENT,
                AgentCapability.DESIGN,
                AgentCapability.DOCUMENTATION,
            ],
            workspace_path=workspace_path,
        )

        self.component_templates = {
            "card": self._card_template,
            "form": self._form_template,
            "modal": self._modal_template,
            "dashboard": self._dashboard_template,
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute component building task"""
        task_type = task.get("type")

        if task_type == "build_component":
            return await self.build_component(task.get("spec"))
        elif task_type == "refactor_component":
            return await self.refactor_component(
                task.get("component_path"), task.get("improvements")
            )
        elif task_type == "add_feature":
            return await self.add_feature(task.get("component_path"), task.get("feature_spec"))
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def build_component(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a React component from specification

        Args:
            spec: Component specification including:
                - name: Component name
                - type: Component type (card, form, modal, etc.)
                - props: Expected props interface
                - features: List of features to include
                - styling: Tailwind classes and theme

        Returns:
            Component build result with file path and code
        """
        component_name = spec.get("name", "UnnamedComponent")
        component_type = spec.get("type", "generic")

        print(f"[{self.agent_id}] Building component: {component_name}")
        print(f"  Type: {component_type}")

        # Generate component code
        code = await self._generate_component_code(spec)

        # Create props interface
        props_interface = self._generate_props_interface(spec.get("props", {}))

        # Add styling
        styled_code = self._apply_tailwind_styling(code, spec.get("styling", {}))

        # Add animations if requested
        if spec.get("animations", False):
            styled_code = self._add_framer_motion(styled_code, spec.get("animation_config", {}))

        result = {
            "status": "completed",
            "component_name": component_name,
            "code": styled_code,
            "props_interface": props_interface,
            "file_suggested": f"{component_name}.tsx",
            "dependencies": self._get_dependencies(spec),
            "usage_example": self._generate_usage_example(component_name, spec.get("props", {})),
        }

        self._log_message(MessageType.STATUS, f"Component {component_name} built successfully")

        return result

    async def _generate_component_code(self, spec: Dict[str, Any]) -> str:
        """Generate base component code"""
        component_type = spec.get("type", "generic")
        template_func = self.component_templates.get(component_type, self._generic_template)
        return template_func(spec)

    def _card_template(self, spec: Dict[str, Any]) -> str:
        """Template for card components"""
        name = spec.get("name", "Card")
        return f"""
import {{ motion }} from 'framer-motion';

interface {name}Props {{
  title?: string;
  children?: React.ReactNode;
  className?: string;
}}

export default function {name}({{ title, children, className = '' }}: {name}Props) {{
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={{`bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 ${{className}}`}}
    >
      {{title && <h3 className="text-xl font-semibold text-white mb-4">{{title}}</h3>}}
      {{children}}
    </motion.div>
  );
}}
"""

    def _form_template(self, spec: Dict[str, Any]) -> str:
        """Template for form components"""
        name = spec.get("name", "Form")
        return f"""
import {{ useState }} from 'react';
import {{ motion }} from 'framer-motion';

interface {name}Props {{
  onSubmit: (data: any) => void;
  isLoading?: boolean;
}}

export default function {name}({{ onSubmit, isLoading = false }}: {name}Props) {{
  const [formData, setFormData] = useState({{}});

  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    onSubmit(formData);
  }};

  return (
    <form onSubmit={{handleSubmit}} className="space-y-4">
      {{/* Form fields here */}}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        type="submit"
        disabled={{isLoading}}
        className="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg"
      >
        {{isLoading ? 'Submitting...' : 'Submit'}}
      </motion.button>
    </form>
  );
}}
"""

    def _modal_template(self, spec: Dict[str, Any]) -> str:
        """Template for modal components"""
        name = spec.get("name", "Modal")
        return f"""
import {{ motion, AnimatePresence }} from 'framer-motion';
import {{ XMarkIcon }} from '@heroicons/react/24/outline';

interface {name}Props {{
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}}

export default function {name}({{ isOpen, onClose, title, children }}: {name}Props) {{
  return (
    <AnimatePresence>
      {{isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={{onClose}}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 flex items-center justify-center z-50 p-4"
          >
            <div className="bg-slate-900 rounded-xl p-6 max-w-2xl w-full border border-white/20">
              <div className="flex items-center justify-between mb-4">
                {{title && <h2 className="text-2xl font-bold text-white">{{title}}</h2>}}
                <button onClick={{onClose}} className="p-2 hover:bg-white/10 rounded-lg">
                  <XMarkIcon className="w-6 h-6 text-white" />
                </button>
              </div>
              {{children}}
            </div>
          </motion.div>
        </>
      )}}
    </AnimatePresence>
  );
}}
"""

    def _dashboard_template(self, spec: Dict[str, Any]) -> str:
        """Template for dashboard components"""
        name = spec.get("name", "Dashboard")
        return f"""
import {{ motion }} from 'framer-motion';

interface {name}Props {{
  stats?: Array<{{ label: string; value: string | number; icon?: React.ReactNode }}>;
  children?: React.ReactNode;
}}

export default function {name}({{ stats = [], children }}: {name}Props) {{
  return (
    <div className="space-y-6">
      {{stats.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {{stats.map((stat, index) => (
            <motion.div
              key={{index}}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">{{stat.label}}</p>
                  <p className="text-3xl font-bold text-white mt-1">{{stat.value}}</p>
                </div>
                {{stat.icon && <div className="text-purple-400">{{stat.icon}}</div>}}
              </div>
            </motion.div>
          ))}}
        </div>
      )}}
      {{children}}
    </div>
  );
}}
"""

    def _generic_template(self, spec: Dict[str, Any]) -> str:
        """Generic component template"""
        name = spec.get("name", "Component")
        return f"""
interface {name}Props {{
  // Define props here
}}

export default function {name}(props: {name}Props) {{
  return (
    <div className="component">
      {{/* Component content */}}
    </div>
  );
}}
"""

    def _generate_props_interface(self, props: Dict[str, str]) -> str:
        """Generate TypeScript props interface"""
        if not props:
            return ""

        interface_lines = []
        for prop_name, prop_type in props.items():
            interface_lines.append(f"  {prop_name}: {prop_type};")

        return "\n".join(interface_lines)

    def _apply_tailwind_styling(self, code: str, styling: Dict[str, Any]) -> str:
        """Apply Tailwind CSS classes"""
        # In production, this would intelligently add/modify Tailwind classes
        return code

    def _add_framer_motion(self, code: str, animation_config: Dict[str, Any]) -> str:
        """Add Framer Motion animations"""
        # In production, this would add motion components and variants
        return code

    def _get_dependencies(self, spec: Dict[str, Any]) -> List[str]:
        """Get required dependencies"""
        deps = ["react", "framer-motion"]

        if spec.get("uses_icons", True):
            deps.append("@heroicons/react")

        return deps

    def _generate_usage_example(self, component_name: str, props: Dict[str, Any]) -> str:
        """Generate usage example"""
        props_example = ", ".join([f"{k}={{...}}" for k in props.keys()])
        return f"<{component_name} {props_example} />"
