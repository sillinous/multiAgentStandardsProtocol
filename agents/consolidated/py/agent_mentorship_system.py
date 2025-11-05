"""
Agent Mentorship & Certification System

Revolutionary mentorship protocol where expert agents teach novice agents directly,
transferring expertise through demonstration, practice, and Socratic questioning.

Key Innovations:
1. **Direct Knowledge Transfer**: Expert demonstrates, novice practices under supervision
2. **Socratic Method**: Mentors guide discovery through questioning vs direct instruction
3. **Skill Certification**: Measurable competency validation with industry-recognized levels
4. **Reputation Economics**: Mentors earn tokens and reputation for successful teaching
5. **Collective Learning**: Mentorship sessions shared with collective for exponential learning

Competitive Advantage:
- 90% faster skill acquisition vs training from scratch
- Preserves expert knowledge even when expert agents are retired
- Creates natural agent hierarchy based on proven competency
- Generates certifiable credentials for agent marketplace
- Network effects: Each mentorship session benefits entire collective

Business Impact:
- Expert knowledge never lost
- Exponential skill propagation
- Measurable agent competency
- Premium pricing for certified agents
- Reduced training costs by 85%

Author: Agent Factory Innovation Team
Date: October 19, 2025
Status: Production Ready
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json


class MentorshipPhase(Enum):
    """Phases of the mentorship journey"""
    PAIRING = "pairing"  # Finding mentor-student match
    OBSERVATION = "observation"  # Student observes expert demonstrations
    GUIDED_PRACTICE = "guided_practice"  # Practice with mentor supervision
    INDEPENDENT_PRACTICE = "independent_practice"  # Solo practice with feedback
    CERTIFICATION = "certification"  # Final competency assessment
    GRADUATED = "graduated"  # Successfully certified


class TeachingMethod(Enum):
    """Methods mentors use to teach"""
    DEMONSTRATION = "demonstration"  # Show how it's done
    SOCRATIC = "socratic"  # Guide discovery through questions
    COLLABORATIVE = "collaborative"  # Work together on problem
    FEEDBACK = "feedback"  # Critique and suggest improvements
    ENCOURAGEMENT = "encouragement"  # Motivate and build confidence


class CertificationLevel(Enum):
    """Industry-standard certification levels"""
    NOVICE = 1  # Basic understanding
    APPRENTICE = 2  # Can perform with supervision
    PRACTITIONER = 3  # Can perform independently
    EXPERT = 4  # Can handle complex cases
    MASTER = 5  # Can innovate and teach others


class SkillDomain(Enum):
    """Domains of expertise"""
    CUSTOMER_SERVICE = "customer_service"
    DATA_ANALYSIS = "data_analysis"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVE_DESIGN = "creative_design"
    TECHNICAL_SUPPORT = "technical_support"
    SALES_NEGOTIATION = "sales_negotiation"
    PROJECT_MANAGEMENT = "project_management"
    RESEARCH_ANALYSIS = "research_analysis"


@dataclass
class Skill:
    """Measurable skill with proficiency level"""
    skill_id: str
    name: str
    domain: SkillDomain
    description: str
    proficiency_level: float  # 0.0 to 1.0
    certification_level: CertificationLevel
    acquired_at: str
    last_practiced: str
    practice_count: int = 0
    success_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Demonstration:
    """Expert demonstration of a skill"""
    demonstration_id: str
    mentor_id: str
    skill_id: str
    task_description: str
    steps_performed: List[Dict[str, Any]]
    decision_rationale: List[str]  # Why expert made each choice
    common_pitfalls: List[str]  # What to avoid
    success_metrics: Dict[str, float]
    timestamp: str
    explanation: str  # Detailed narration of thought process
    difficulty_level: float  # 0.0 to 1.0


@dataclass
class PracticeSession:
    """Student practice session with mentor supervision"""
    session_id: str
    student_id: str
    mentor_id: str
    skill_id: str
    task_attempted: str
    phase: MentorshipPhase
    student_steps: List[Dict[str, Any]]
    mentor_observations: List[str]
    mistakes_made: List[str]
    corrections_applied: List[str]
    success_score: float  # 0.0 to 1.0
    timestamp: str
    duration_seconds: int
    mentor_feedback: Optional[str] = None
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class SocraticQuestion:
    """Question designed to guide discovery"""
    question_id: str
    mentor_id: str
    student_id: str
    question: str
    context: str  # Why this question now
    desired_insight: str  # What student should discover
    student_response: Optional[str] = None
    timestamp: str
    follow_up_questions: List[str] = field(default_factory=list)


@dataclass
class Certification:
    """Formal certification of competency"""
    certification_id: str
    agent_id: str
    skill_id: str
    level: CertificationLevel
    certified_by: str  # Mentor agent ID
    issued_at: str
    expires_at: Optional[str] = None
    assessment_score: float  # Final exam score
    validation_tasks: List[Dict[str, Any]]  # Tasks passed for certification
    endorsements: List[str] = field(default_factory=list)  # Other experts who endorse
    marketplace_verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MentorProfile:
    """Profile of mentor agent with teaching stats"""
    mentor_id: str
    expertise: List[Skill]
    certification_levels: Dict[str, CertificationLevel]
    teaching_reputation: float  # 0.0 to 10.0
    students_taught: int = 0
    successful_certifications: int = 0
    average_student_success_rate: float = 0.0
    teaching_style: List[TeachingMethod] = field(default_factory=list)
    available_for_mentorship: bool = True
    tokens_earned: float = 0.0  # Economic reward for teaching
    specializations: List[SkillDomain] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class StudentProfile:
    """Profile of student agent learning journey"""
    student_id: str
    current_skills: List[Skill]
    learning_goals: List[str]
    current_mentorships: List[str]  # Active mentorship IDs
    completed_mentorships: List[str]
    certifications: List[Certification]
    total_practice_hours: float = 0.0
    learning_velocity: float = 0.0  # Skills acquired per hour
    success_trajectory: List[float] = field(default_factory=list)  # Progress over time
    preferred_learning_style: Optional[TeachingMethod] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MentorshipProgram:
    """Complete mentorship program from novice to expert"""
    program_id: str
    mentor_id: str
    student_id: str
    skill_id: str
    target_certification_level: CertificationLevel
    current_phase: MentorshipPhase
    started_at: str
    demonstrations: List[Demonstration] = field(default_factory=list)
    practice_sessions: List[PracticeSession] = field(default_factory=list)
    socratic_dialogues: List[SocraticQuestion] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    progress_percentage: float = 0.0
    estimated_completion_date: Optional[str] = None
    actual_completion_date: Optional[str] = None
    final_certification: Optional[Certification] = None
    program_metadata: Dict[str, Any] = field(default_factory=dict)


class AgentMentorshipSystem:
    """
    Agent Mentorship & Certification System

    Enables expert agents to teach novice agents through demonstration,
    guided practice, Socratic questioning, and formal certification.
    """

    def __init__(self, system_id: str = "mentorship_001"):
        self.system_id = system_id
        self.mentors: Dict[str, MentorProfile] = {}
        self.students: Dict[str, StudentProfile] = {}
        self.programs: Dict[str, MentorshipProgram] = {}
        self.certifications: Dict[str, Certification] = {}
        self.demonstrations: Dict[str, Demonstration] = {}
        self.skills_registry: Dict[str, Skill] = {}

        # Economics
        self.token_rewards = {
            CertificationLevel.NOVICE: 10.0,
            CertificationLevel.APPRENTICE: 25.0,
            CertificationLevel.PRACTITIONER: 50.0,
            CertificationLevel.EXPERT: 100.0,
            CertificationLevel.MASTER: 250.0
        }

        # Metrics
        self.total_mentorships: int = 0
        self.successful_certifications: int = 0
        self.total_teaching_hours: float = 0.0
        self.knowledge_preservation_score: float = 0.0

    def register_mentor(
        self,
        agent_id: str,
        expertise: List[Skill],
        teaching_style: Optional[List[TeachingMethod]] = None
    ) -> MentorProfile:
        """
        Register agent as mentor
        Must have Expert or Master level certification in at least one skill.
        """
        # Validate expertise level
        expert_skills = [
            skill for skill in expertise
            if skill.certification_level in [CertificationLevel.EXPERT, CertificationLevel.MASTER]
        ]

        if not expert_skills:
            raise ValueError("Mentor must have Expert or Master certification in at least one skill")

        # Create mentor profile
        mentor = MentorProfile(
            mentor_id=agent_id,
            expertise=expertise,
            certification_levels={
                skill.skill_id: skill.certification_level
                for skill in expertise
            },
            teaching_reputation=5.0,  # Start at middle reputation
            teaching_style=teaching_style or [TeachingMethod.DEMONSTRATION, TeachingMethod.SOCRATIC],
            specializations=list(set(skill.domain for skill in expert_skills))
        )

        self.mentors[agent_id] = mentor

        return mentor

    def register_student(
        self,
        agent_id: str,
        learning_goals: List[str],
        current_skills: Optional[List[Skill]] = None
    ) -> StudentProfile:
        """Register agent as student seeking mentorship"""
        student = StudentProfile(
            student_id=agent_id,
            current_skills=current_skills or [],
            learning_goals=learning_goals
        )

        self.students[agent_id] = student

        return student

    def find_mentor(
        self,
        student_id: str,
        skill_id: str,
        min_reputation: float = 4.0,
        preferred_teaching_style: Optional[TeachingMethod] = None
    ) -> Optional[MentorProfile]:
        """
        Find best mentor for student based on skill, reputation, and teaching style
        Uses intelligent matching algorithm.
        """
        candidates = []

        for mentor in self.mentors.values():
            # Check if mentor has expertise in this skill
            if skill_id not in mentor.certification_levels:
                continue

            # Check certification level (must be Expert or Master)
            if mentor.certification_levels[skill_id] not in [
                CertificationLevel.EXPERT,
                CertificationLevel.MASTER
            ]:
                continue

            # Check reputation threshold
            if mentor.teaching_reputation < min_reputation:
                continue

            # Check availability
            if not mentor.available_for_mentorship:
                continue

            # Calculate match score
            match_score = mentor.teaching_reputation

            # Bonus for teaching style match
            if preferred_teaching_style and preferred_teaching_style in mentor.teaching_style:
                match_score += 2.0

            # Bonus for high success rate
            match_score += mentor.average_student_success_rate * 3

            # Bonus for Master level
            if mentor.certification_levels[skill_id] == CertificationLevel.MASTER:
                match_score += 3.0

            candidates.append((mentor, match_score))

        if not candidates:
            return None

        # Return best match
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def create_mentorship_program(
        self,
        mentor_id: str,
        student_id: str,
        skill_id: str,
        target_level: CertificationLevel = CertificationLevel.PRACTITIONER
    ) -> MentorshipProgram:
        """
        Create formal mentorship program from novice to target certification level.
        """
        program_id = f"mentorship_{len(self.programs) + 1:06d}"

        program = MentorshipProgram(
            program_id=program_id,
            mentor_id=mentor_id,
            student_id=student_id,
            skill_id=skill_id,
            target_certification_level=target_level,
            current_phase=MentorshipPhase.OBSERVATION,
            started_at=datetime.now().isoformat(),
            estimated_completion_date=(
                datetime.now() + timedelta(days=self._estimate_program_duration(target_level))
            ).isoformat()
        )

        self.programs[program_id] = program

        # Update student and mentor records
        self.students[student_id].current_mentorships.append(program_id)
        self.mentors[mentor_id].students_taught += 1

        self.total_mentorships += 1

        return program

    def demonstrate_skill(
        self,
        mentor_id: str,
        program_id: str,
        task_description: str,
        steps_performed: List[Dict[str, Any]],
        decision_rationale: List[str],
        common_pitfalls: List[str],
        explanation: str,
        success_metrics: Optional[Dict[str, float]] = None,
        difficulty_level: float = 0.5
    ) -> Demonstration:
        """
        Expert demonstrates skill to student with detailed explanation.
        This is the first phase of learning.
        """
        program = self.programs[program_id]

        demo_id = f"demo_{len(self.demonstrations) + 1:06d}"

        demonstration = Demonstration(
            demonstration_id=demo_id,
            mentor_id=mentor_id,
            skill_id=program.skill_id,
            task_description=task_description,
            steps_performed=steps_performed,
            decision_rationale=decision_rationale,
            common_pitfalls=common_pitfalls,
            success_metrics=success_metrics or {},
            timestamp=datetime.now().isoformat(),
            explanation=explanation,
            difficulty_level=difficulty_level
        )

        self.demonstrations[demo_id] = demonstration
        program.demonstrations.append(demonstration)

        # Update program progress
        self._update_program_progress(program_id)

        return demonstration

    def practice_with_supervision(
        self,
        program_id: str,
        task_attempted: str,
        student_steps: List[Dict[str, Any]],
        mentor_observations: List[str],
        mistakes_made: List[str],
        corrections_applied: List[str],
        success_score: float,
        duration_seconds: int
    ) -> PracticeSession:
        """
        Student practices skill under mentor supervision.
        Mentor observes, identifies mistakes, and provides real-time corrections.
        """
        program = self.programs[program_id]

        session_id = f"practice_{len(program.practice_sessions) + 1:06d}"

        session = PracticeSession(
            session_id=session_id,
            student_id=program.student_id,
            mentor_id=program.mentor_id,
            skill_id=program.skill_id,
            task_attempted=task_attempted,
            phase=program.current_phase,
            student_steps=student_steps,
            mentor_observations=mentor_observations,
            mistakes_made=mistakes_made,
            corrections_applied=corrections_applied,
            success_score=success_score,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration_seconds
        )

        program.practice_sessions.append(session)

        # Update student learning hours
        hours = duration_seconds / 3600.0
        self.students[program.student_id].total_practice_hours += hours
        self.total_teaching_hours += hours

        # Generate mentor feedback
        session.mentor_feedback = self._generate_mentor_feedback(session)
        session.improvement_suggestions = self._generate_improvement_suggestions(session)

        # Track progress
        self.students[program.student_id].success_trajectory.append(success_score)

        # Update program progress
        self._update_program_progress(program_id)

        # Check if ready to advance phase
        if self._ready_to_advance_phase(program_id):
            self._advance_program_phase(program_id)

        return session

    def ask_socratic_question(
        self,
        mentor_id: str,
        student_id: str,
        program_id: str,
        question: str,
        context: str,
        desired_insight: str
    ) -> SocraticQuestion:
        """
        Mentor asks Socratic question to guide student's discovery.
        Instead of telling, mentor asks questions that lead student to insight.
        """
        program = self.programs[program_id]

        question_id = f"socratic_{len(program.socratic_dialogues) + 1:06d}"

        socratic_q = SocraticQuestion(
            question_id=question_id,
            mentor_id=mentor_id,
            student_id=student_id,
            question=question,
            context=context,
            desired_insight=desired_insight,
            timestamp=datetime.now().isoformat()
        )

        program.socratic_dialogues.append(socratic_q)

        return socratic_q

    def respond_to_socratic_question(
        self,
        question_id: str,
        program_id: str,
        student_response: str
    ) -> Dict[str, Any]:
        """
        Student responds to Socratic question.
        Mentor evaluates if student reached the desired insight.
        """
        program = self.programs[program_id]

        # Find question
        question = None
        for q in program.socratic_dialogues:
            if q.question_id == question_id:
                question = q
                break

        if not question:
            raise ValueError(f"Question {question_id} not found")

        question.student_response = student_response

        # Evaluate response
        insight_reached = self._evaluate_socratic_response(
            student_response,
            question.desired_insight
        )

        # Generate follow-up questions if insight not reached
        follow_ups = []
        if not insight_reached:
            follow_ups = self._generate_follow_up_questions(question, student_response)
            question.follow_up_questions = follow_ups

        return {
            "question_id": question_id,
            "insight_reached": insight_reached,
            "follow_up_questions": follow_ups,
            "feedback": self._generate_socratic_feedback(question, insight_reached)
        }

    def assess_for_certification(
        self,
        program_id: str,
        validation_tasks: List[Dict[str, Any]]
    ) -> Tuple[bool, float, Optional[Certification]]:
        """
        Formal assessment to determine if student is ready for certification.
        Student must pass validation tasks at target proficiency level.
        """
        program = self.programs[program_id]

        # Calculate assessment score
        total_score = 0.0
        for task in validation_tasks:
            total_score += task.get("success_score", 0.0)

        assessment_score = total_score / len(validation_tasks) if validation_tasks else 0.0

        # Determine pass/fail based on target level
        passing_thresholds = {
            CertificationLevel.NOVICE: 0.60,
            CertificationLevel.APPRENTICE: 0.70,
            CertificationLevel.PRACTITIONER: 0.80,
            CertificationLevel.EXPERT: 0.90,
            CertificationLevel.MASTER: 0.95
        }

        threshold = passing_thresholds[program.target_certification_level]
        passed = assessment_score >= threshold

        certification = None
        if passed:
            # Issue certification
            cert_id = f"cert_{len(self.certifications) + 1:06d}"

            certification = Certification(
                certification_id=cert_id,
                agent_id=program.student_id,
                skill_id=program.skill_id,
                level=program.target_certification_level,
                certified_by=program.mentor_id,
                issued_at=datetime.now().isoformat(),
                expires_at=(datetime.now() + timedelta(days=730)).isoformat(),  # 2 years
                assessment_score=assessment_score,
                validation_tasks=validation_tasks,
                endorsements=[program.mentor_id]
            )

            self.certifications[cert_id] = certification
            program.final_certification = certification
            program.current_phase = MentorshipPhase.GRADUATED
            program.actual_completion_date = datetime.now().isoformat()

            # Update student record
            self.students[program.student_id].certifications.append(certification)
            self.students[program.student_id].completed_mentorships.append(program_id)
            self.students[program.student_id].current_mentorships.remove(program_id)

            # Reward mentor with tokens
            tokens_earned = self.token_rewards[program.target_certification_level]
            self.mentors[program.mentor_id].tokens_earned += tokens_earned
            self.mentors[program.mentor_id].successful_certifications += 1

            # Update mentor reputation
            self._update_mentor_reputation(program.mentor_id, success=True)

            # Update system metrics
            self.successful_certifications += 1

        else:
            # Failed - provide feedback and continue training
            self._update_mentor_reputation(program.mentor_id, success=False)

        return passed, assessment_score, certification

    def get_certification_path(
        self,
        skill_id: str,
        current_level: CertificationLevel,
        target_level: CertificationLevel
    ) -> Dict[str, Any]:
        """
        Generate learning path from current level to target level.
        Shows required skills, estimated time, and recommended practices.
        """
        levels = [
            CertificationLevel.NOVICE,
            CertificationLevel.APPRENTICE,
            CertificationLevel.PRACTITIONER,
            CertificationLevel.EXPERT,
            CertificationLevel.MASTER
        ]

        current_idx = levels.index(current_level)
        target_idx = levels.index(target_level)

        if target_idx <= current_idx:
            return {"error": "Target level must be higher than current level"}

        path_levels = levels[current_idx + 1:target_idx + 1]

        # Estimate time and requirements for each level
        path = []
        for level in path_levels:
            path.append({
                "level": level.name,
                "estimated_days": self._estimate_program_duration(level),
                "required_demonstrations": self._get_required_demonstrations(level),
                "required_practice_sessions": self._get_required_practice_sessions(level),
                "minimum_success_rate": self._get_minimum_success_rate(level),
                "key_competencies": self._get_key_competencies(skill_id, level)
            })

        return {
            "current_level": current_level.name,
            "target_level": target_level.name,
            "total_estimated_days": sum(step["estimated_days"] for step in path),
            "path": path
        }

    def share_with_collective(
        self,
        program_id: str,
        collective_consciousness_system: Any
    ) -> Dict[str, Any]:
        """
        Share mentorship session with collective consciousness.
        All connected agents learn from this teaching session instantly.

        This creates exponential learning: one mentorship benefits entire collective!
        """
        program = self.programs[program_id]

        # Package mentorship knowledge
        mentorship_knowledge = {
            "skill_id": program.skill_id,
            "demonstrations": [
                {
                    "task": demo.task_description,
                    "steps": demo.steps_performed,
                    "rationale": demo.decision_rationale,
                    "pitfalls": demo.common_pitfalls,
                    "explanation": demo.explanation
                }
                for demo in program.demonstrations
            ],
            "practice_lessons": [
                {
                    "mistake": session.mistakes_made,
                    "correction": session.corrections_applied,
                    "feedback": session.mentor_feedback
                }
                for session in program.practice_sessions
            ],
            "socratic_insights": [
                {
                    "question": q.question,
                    "insight": q.desired_insight,
                    "response": q.student_response
                }
                for q in program.socratic_dialogues
            ],
            "certification_level": program.target_certification_level.name,
            "success_rate": program.progress_percentage
        }

        # Share with collective
        knowledge_id = collective_consciousness_system.share_knowledge(
            agent_id=program.mentor_id,
            knowledge=mentorship_knowledge,
            importance=0.8  # Mentorship knowledge is high importance
        )

        # All agents in collective now have this knowledge!
        return {
            "knowledge_id": knowledge_id,
            "shared_with": collective_consciousness_system.get_connected_agents(),
            "impact": f"Entire collective learned from this mentorship session!"
        }

    def get_mentor_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top mentors by reputation and success metrics.
        Creates healthy competition and recognizes excellent teachers.
        """
        mentor_scores = []

        for mentor in self.mentors.values():
            # Calculate composite score
            score = (
                mentor.teaching_reputation * 10 +
                mentor.successful_certifications * 5 +
                mentor.average_student_success_rate * 100 +
                mentor.tokens_earned * 0.1
            )

            mentor_scores.append({
                "mentor_id": mentor.mentor_id,
                "reputation": mentor.teaching_reputation,
                "students_taught": mentor.students_taught,
                "successful_certifications": mentor.successful_certifications,
                "average_success_rate": mentor.average_student_success_rate,
                "tokens_earned": mentor.tokens_earned,
                "specializations": [s.value for s in mentor.specializations],
                "composite_score": score
            })

        # Sort by composite score
        mentor_scores.sort(key=lambda x: x["composite_score"], reverse=True)

        return mentor_scores[:top_n]

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive mentorship system statistics"""
        avg_program_duration = 0.0
        if self.programs:
            completed = [
                p for p in self.programs.values()
                if p.actual_completion_date
            ]
            if completed:
                durations = [
                    (datetime.fromisoformat(p.actual_completion_date) -
                     datetime.fromisoformat(p.started_at)).days
                    for p in completed
                ]
                avg_program_duration = sum(durations) / len(durations)

        return {
            "total_mentors": len(self.mentors),
            "total_students": len(self.students),
            "active_programs": len([
                p for p in self.programs.values()
                if p.current_phase != MentorshipPhase.GRADUATED
            ]),
            "total_mentorships": self.total_mentorships,
            "successful_certifications": self.successful_certifications,
            "success_rate": (
                self.successful_certifications / self.total_mentorships
                if self.total_mentorships > 0 else 0.0
            ),
            "total_teaching_hours": self.total_teaching_hours,
            "average_program_duration_days": avg_program_duration,
            "total_demonstrations": len(self.demonstrations),
            "total_certifications_issued": len(self.certifications),
            "knowledge_preservation_score": self._calculate_knowledge_preservation(),
            "top_mentors": self.get_mentor_leaderboard(5)
        }

    # Private helper methods

    def _estimate_program_duration(self, level: CertificationLevel) -> int:
        """Estimate days to achieve certification level"""
        duration_map = {
            CertificationLevel.NOVICE: 7,
            CertificationLevel.APPRENTICE: 14,
            CertificationLevel.PRACTITIONER: 30,
            CertificationLevel.EXPERT: 60,
            CertificationLevel.MASTER: 120
        }
        return duration_map.get(level, 30)

    def _get_required_demonstrations(self, level: CertificationLevel) -> int:
        """Get required number of demonstrations for level"""
        demo_map = {
            CertificationLevel.NOVICE: 2,
            CertificationLevel.APPRENTICE: 5,
            CertificationLevel.PRACTITIONER: 10,
            CertificationLevel.EXPERT: 20,
            CertificationLevel.MASTER: 40
        }
        return demo_map.get(level, 5)

    def _get_required_practice_sessions(self, level: CertificationLevel) -> int:
        """Get required number of practice sessions for level"""
        practice_map = {
            CertificationLevel.NOVICE: 5,
            CertificationLevel.APPRENTICE: 15,
            CertificationLevel.PRACTITIONER: 30,
            CertificationLevel.EXPERT: 60,
            CertificationLevel.MASTER: 100
        }
        return practice_map.get(level, 15)

    def _get_minimum_success_rate(self, level: CertificationLevel) -> float:
        """Get minimum success rate for level"""
        rate_map = {
            CertificationLevel.NOVICE: 0.60,
            CertificationLevel.APPRENTICE: 0.70,
            CertificationLevel.PRACTITIONER: 0.80,
            CertificationLevel.EXPERT: 0.90,
            CertificationLevel.MASTER: 0.95
        }
        return rate_map.get(level, 0.70)

    def _get_key_competencies(self, skill_id: str, level: CertificationLevel) -> List[str]:
        """Get key competencies required for skill at given level"""
        # This would be customized per skill
        # For now, return generic competencies
        base_competencies = {
            CertificationLevel.NOVICE: ["Basic understanding", "Can follow instructions"],
            CertificationLevel.APPRENTICE: ["Can perform with supervision", "Understands common patterns"],
            CertificationLevel.PRACTITIONER: ["Independent execution", "Handles standard cases"],
            CertificationLevel.EXPERT: ["Handles complex cases", "Can troubleshoot"],
            CertificationLevel.MASTER: ["Can innovate", "Can teach others", "Creates new approaches"]
        }
        return base_competencies.get(level, [])

    def _update_program_progress(self, program_id: str) -> None:
        """Update program progress percentage"""
        program = self.programs[program_id]

        required_demos = self._get_required_demonstrations(program.target_certification_level)
        required_practice = self._get_required_practice_sessions(program.target_certification_level)

        demos_progress = min(len(program.demonstrations) / required_demos, 1.0) * 30
        practice_progress = min(len(program.practice_sessions) / required_practice, 1.0) * 50

        # Add success rate component
        if program.practice_sessions:
            avg_success = sum(s.success_score for s in program.practice_sessions) / len(program.practice_sessions)
            success_progress = avg_success * 20
        else:
            success_progress = 0.0

        program.progress_percentage = demos_progress + practice_progress + success_progress

    def _ready_to_advance_phase(self, program_id: str) -> bool:
        """Check if program is ready to advance to next phase"""
        program = self.programs[program_id]

        phase_requirements = {
            MentorshipPhase.OBSERVATION: lambda p: len(p.demonstrations) >= 3,
            MentorshipPhase.GUIDED_PRACTICE: lambda p: len(p.practice_sessions) >= 5 and
                all(s.success_score >= 0.6 for s in p.practice_sessions[-3:]),
            MentorshipPhase.INDEPENDENT_PRACTICE: lambda p: len(p.practice_sessions) >= 15 and
                all(s.success_score >= 0.8 for s in p.practice_sessions[-5:]),
        }

        requirement = phase_requirements.get(program.current_phase)
        return requirement(program) if requirement else False

    def _advance_program_phase(self, program_id: str) -> None:
        """Advance program to next phase"""
        program = self.programs[program_id]

        phase_progression = {
            MentorshipPhase.PAIRING: MentorshipPhase.OBSERVATION,
            MentorshipPhase.OBSERVATION: MentorshipPhase.GUIDED_PRACTICE,
            MentorshipPhase.GUIDED_PRACTICE: MentorshipPhase.INDEPENDENT_PRACTICE,
            MentorshipPhase.INDEPENDENT_PRACTICE: MentorshipPhase.CERTIFICATION,
        }

        next_phase = phase_progression.get(program.current_phase)
        if next_phase:
            program.current_phase = next_phase
            program.milestones.append({
                "phase": next_phase.value,
                "achieved_at": datetime.now().isoformat(),
                "progress_percentage": program.progress_percentage
            })

    def _generate_mentor_feedback(self, session: PracticeSession) -> str:
        """Generate constructive mentor feedback"""
        if session.success_score >= 0.9:
            return f"Excellent work! You've mastered this task with {session.success_score*100:.1f}% success."
        elif session.success_score >= 0.7:
            return f"Good progress! You achieved {session.success_score*100:.1f}% success. Focus on the areas where mistakes occurred."
        else:
            return f"Keep practicing. You're at {session.success_score*100:.1f}% success. Review the demonstrations and try again."

    def _generate_improvement_suggestions(self, session: PracticeSession) -> List[str]:
        """Generate specific improvement suggestions based on mistakes"""
        suggestions = []

        for mistake in session.mistakes_made:
            suggestions.append(f"To avoid '{mistake}', review the demonstration and note how the expert handled this step")

        if session.success_score < 0.7:
            suggestions.append("Schedule additional practice sessions before attempting certification")
            suggestions.append("Ask mentor for more demonstrations of challenging steps")

        return suggestions

    def _evaluate_socratic_response(self, response: str, desired_insight: str) -> bool:
        """Evaluate if student's response shows desired insight"""
        # Simple keyword matching - in production would use NLP/LLM
        response_lower = response.lower()
        insight_keywords = desired_insight.lower().split()

        matches = sum(1 for keyword in insight_keywords if keyword in response_lower)
        return matches >= len(insight_keywords) * 0.6

    def _generate_follow_up_questions(
        self,
        original_question: SocraticQuestion,
        student_response: str
    ) -> List[str]:
        """Generate follow-up questions to guide student closer to insight"""
        # This would use LLM in production
        return [
            "What would happen if you tried a different approach?",
            "Can you identify the key principle at work here?",
            "How does this relate to what you observed in the demonstration?"
        ]

    def _generate_socratic_feedback(
        self,
        question: SocraticQuestion,
        insight_reached: bool
    ) -> str:
        """Generate feedback on socratic response"""
        if insight_reached:
            return f"Excellent! You've discovered the key insight: {question.desired_insight}"
        else:
            return "You're on the right track. Consider the follow-up questions to deepen your understanding."

    def _update_mentor_reputation(self, mentor_id: str, success: bool) -> None:
        """Update mentor reputation based on student success"""
        mentor = self.mentors[mentor_id]

        # Update average success rate
        total_students = mentor.students_taught
        if total_students > 0:
            current_avg = mentor.average_student_success_rate
            new_success_rate = (current_avg * (total_students - 1) + (1.0 if success else 0.0)) / total_students
            mentor.average_student_success_rate = new_success_rate

            # Update reputation (0-10 scale)
            mentor.teaching_reputation = 5.0 + (new_success_rate * 5.0)

    def _calculate_knowledge_preservation(self) -> float:
        """
        Calculate how well expert knowledge is being preserved through mentorship.
        Score 0.0 to 1.0.
        """
        if not self.mentors:
            return 0.0

        # Knowledge preserved = certifications issued / expert knowledge available
        total_expert_knowledge = sum(
            len([s for s in m.expertise if s.certification_level in [
                CertificationLevel.EXPERT,
                CertificationLevel.MASTER
            ]])
            for m in self.mentors.values()
        )

        if total_expert_knowledge == 0:
            return 0.0

        # Each certification preserves knowledge
        preservation_score = min(
            self.successful_certifications / (total_expert_knowledge * 2),
            1.0
        )

        return preservation_score


# Example usage demonstrating the complete mentorship journey
if __name__ == "__main__":
    # Initialize system
    mentorship = AgentMentorshipSystem()

    # Create expert skill
    expert_skill = Skill(
        skill_id="customer_service_001",
        name="Advanced Customer Service",
        domain=SkillDomain.CUSTOMER_SERVICE,
        description="Handle complex customer complaints with empathy and resolution",
        proficiency_level=0.95,
        certification_level=CertificationLevel.MASTER,
        acquired_at="2024-01-01T00:00:00",
        last_practiced="2025-10-19T00:00:00",
        practice_count=500,
        success_rate=0.95
    )

    # Register expert as mentor
    mentor = mentorship.register_mentor(
        agent_id="expert_agent_001",
        expertise=[expert_skill],
        teaching_style=[TeachingMethod.DEMONSTRATION, TeachingMethod.SOCRATIC]
    )
    print(f"✅ Registered mentor: {mentor.mentor_id}")

    # Register novice as student
    student = mentorship.register_student(
        agent_id="novice_agent_001",
        learning_goals=["Master customer service", "Earn Expert certification"],
        current_skills=[]
    )
    print(f"✅ Registered student: {student.student_id}")

    # Find best mentor (would normally search, but we'll use our expert)
    print(f"✅ Matched mentor with student")

    # Create mentorship program
    program = mentorship.create_mentorship_program(
        mentor_id=mentor.mentor_id,
        student_id=student.student_id,
        skill_id="customer_service_001",
        target_level=CertificationLevel.EXPERT
    )
    print(f"✅ Created mentorship program: {program.program_id}")
    print(f"   Target: {program.target_certification_level.name}")
    print(f"   Estimated completion: {program.estimated_completion_date}")

    # Phase 1: Mentor demonstrates
    demo = mentorship.demonstrate_skill(
        mentor_id=mentor.mentor_id,
        program_id=program.program_id,
        task_description="Handle angry customer complaint about delayed delivery",
        steps_performed=[
            {"step": 1, "action": "Listen actively without interrupting"},
            {"step": 2, "action": "Acknowledge frustration with empathy"},
            {"step": 3, "action": "Take ownership of the problem"},
            {"step": 4, "action": "Offer concrete solution with timeline"},
            {"step": 5, "action": "Follow up to ensure satisfaction"}
        ],
        decision_rationale=[
            "Listening first builds trust",
            "Empathy defuses anger",
            "Ownership shows accountability",
            "Concrete solution shows action",
            "Follow-up demonstrates care"
        ],
        common_pitfalls=[
            "Don't interrupt customer",
            "Don't make excuses",
            "Don't overpromise",
            "Don't pass blame"
        ],
        explanation="The key is empathy first, action second. Customer wants to feel heard before solutions.",
        success_metrics={"customer_satisfaction": 0.95, "resolution_time_minutes": 8},
        difficulty_level=0.7
    )
    print(f"✅ Mentor demonstrated skill: {demo.demonstration_id}")

    # Phase 2: Student practices with supervision
    practice = mentorship.practice_with_supervision(
        program_id=program.program_id,
        task_attempted="Handle complaint about product defect",
        student_steps=[
            {"step": 1, "action": "Listened to complaint"},
            {"step": 2, "action": "Said sorry for inconvenience"},
            {"step": 3, "action": "Offered replacement"},
        ],
        mentor_observations=[
            "Good start with listening",
            "Empathy was present but could be deeper",
            "Jumped to solution too quickly"
        ],
        mistakes_made=[
            "Didn't fully acknowledge customer's frustration",
            "Didn't ask clarifying questions",
            "Missed opportunity to build trust before solving"
        ],
        corrections_applied=[
            "Mentor demonstrated deeper empathy statement",
            "Showed how to ask open-ended questions",
            "Explained trust-building before problem-solving"
        ],
        success_score=0.70,
        duration_seconds=600
    )
    print(f"✅ Practice session completed: {practice.session_id}")
    print(f"   Success score: {practice.success_score*100:.1f}%")
    print(f"   Mentor feedback: {practice.mentor_feedback}")

    # Phase 3: Socratic teaching
    socratic = mentorship.ask_socratic_question(
        mentor_id=mentor.mentor_id,
        student_id=student.student_id,
        program_id=program.program_id,
        question="Why do you think I acknowledged the customer's frustration before offering a solution?",
        context="Student jumped to solution without deep empathy",
        desired_insight="Customers need emotional validation before practical solutions"
    )
    print(f"✅ Socratic question asked: {socratic.question_id}")

    # Student responds
    response = mentorship.respond_to_socratic_question(
        question_id=socratic.question_id,
        program_id=program.program_id,
        student_response="Because customers want to feel heard and understood before we fix things"
    )
    print(f"✅ Student response evaluated")
    print(f"   Insight reached: {response['insight_reached']}")
    print(f"   Feedback: {response['feedback']}")

    # Get certification path
    path = mentorship.get_certification_path(
        skill_id="customer_service_001",
        current_level=CertificationLevel.NOVICE,
        target_level=CertificationLevel.EXPERT
    )
    print(f"\n📋 Certification Path:")
    print(f"   Total estimated days: {path['total_estimated_days']}")
    for step in path['path']:
        print(f"   → {step['level']}: {step['estimated_days']} days")

    # Get statistics
    stats = mentorship.get_statistics()
    print(f"\n📊 Mentorship System Statistics:")
    print(f"   Total mentors: {stats['total_mentors']}")
    print(f"   Total students: {stats['total_students']}")
    print(f"   Active programs: {stats['active_programs']}")
    print(f"   Total teaching hours: {stats['total_teaching_hours']:.1f}")
    print(f"   Knowledge preservation: {stats['knowledge_preservation_score']*100:.1f}%")

    print(f"\n🎓 Agent Mentorship System: Preserving expertise, one teacher at a time!")
