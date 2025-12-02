"""
Smart Recruitment Agent - Example Implementation

Demonstrates AI-powered HR capabilities:
- Intelligent candidate screening
- Resume parsing and skill extraction
- Culture fit assessment
- Interview question generation
- Bias detection and mitigation
- Candidate ranking with explainability

APQC Process: 7.2 - Recruit, Source, and Select Employees
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


@dataclass
class RecruitmentConfig:
    """Configuration for Smart Recruitment Agent"""
    agent_id: str = "smart_recruitment_agent_001"
    agent_name: str = "Smart Recruitment Agent"

    # AI Configuration
    ai_provider: str = "auto"
    enable_bias_detection: bool = True
    enable_culture_fit: bool = True

    # Screening Parameters
    min_match_score: float = 0.6
    max_candidates_per_batch: int = 50
    skill_weight: float = 0.4
    experience_weight: float = 0.3
    culture_fit_weight: float = 0.3

    # Compliance
    enforce_eeoc_compliance: bool = True
    anonymize_initial_screening: bool = True


class SmartRecruitmentAgent:
    """
    AI-Powered Recruitment and Talent Acquisition Agent

    Capabilities:
    - Resume parsing and skill extraction
    - Intelligent candidate matching
    - Bias-aware screening
    - Culture fit assessment
    - Interview scheduling optimization
    - Candidate communication automation

    Integration:
    - Uses HRProcessor from smart_processing
    - APQC Process: 7.2 - Recruit, Source, and Select Employees
    """

    APQC_CATEGORY_ID = "7.0"
    APQC_PROCESS_ID = "7.2"

    def __init__(self, config: Optional[RecruitmentConfig] = None):
        self.config = config or RecruitmentConfig()
        self.state = {
            "candidates_screened": 0,
            "positions_filled": 0,
            "interviews_scheduled": 0,
            "bias_alerts": 0,
            "last_activity": None
        }

    async def screen_candidates(
        self,
        job_requirements: Dict[str, Any],
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Screen candidates using AI-powered analysis

        Args:
            job_requirements: Job description, required skills, experience
            candidates: List of candidate profiles with resumes

        Returns:
            Ranked candidates with detailed assessments
        """
        from superstandard.services.smart_processing import get_processor
        from superstandard.services.ai_service import get_ai_service

        start_time = datetime.now()

        processor = get_processor("hr")
        ai_service = get_ai_service()

        # Extract required skills from job description
        required_skills = await self._extract_job_skills(
            job_requirements,
            ai_service
        )

        # Process each candidate
        assessments = []
        for candidate in candidates[:self.config.max_candidates_per_batch]:
            assessment = await self._assess_candidate(
                candidate,
                job_requirements,
                required_skills,
                processor,
                ai_service
            )
            assessments.append(assessment)

        # Rank candidates
        ranked_candidates = self._rank_candidates(assessments)

        # Bias check
        bias_report = None
        if self.config.enable_bias_detection:
            bias_report = await self._check_for_bias(
                ranked_candidates,
                ai_service
            )

        # Generate interview questions for top candidates
        interview_prep = await self._generate_interview_questions(
            ranked_candidates[:5],
            job_requirements,
            ai_service
        )

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()

        # Update state
        self.state["candidates_screened"] += len(candidates)
        self.state["last_activity"] = datetime.now().isoformat()

        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "apqc_process": self.APQC_PROCESS_ID,
            "job_title": job_requirements.get("title", "Unknown Position"),
            "candidates_processed": len(candidates),
            "ranked_candidates": ranked_candidates,
            "interview_preparation": interview_prep,
            "bias_report": bias_report,
            "metrics": {
                "processing_time_seconds": processing_time,
                "candidates_above_threshold": len([
                    c for c in ranked_candidates
                    if c["overall_score"] >= self.config.min_match_score
                ]),
                "average_match_score": sum(
                    c["overall_score"] for c in ranked_candidates
                ) / len(ranked_candidates) if ranked_candidates else 0
            }
        }

    async def _extract_job_skills(
        self,
        job_requirements: Dict[str, Any],
        ai_service
    ) -> List[Dict[str, Any]]:
        """Extract and categorize required skills from job description"""
        job_desc = job_requirements.get("description", "")
        explicit_skills = job_requirements.get("required_skills", [])

        # Use AI to extract implicit skills
        extraction_result = await ai_service.analyze(
            prompt=f"""Extract all required skills from this job posting:
            Title: {job_requirements.get('title', 'Unknown')}
            Description: {job_desc[:1000]}
            Explicit Skills: {explicit_skills}

            Return skills categorized as:
            - technical: Hard skills (programming, tools, etc.)
            - soft: Communication, leadership, etc.
            - domain: Industry-specific knowledge

            Include importance level (high, medium, low) for each.
            """,
            data={"job": job_requirements}
        )

        skills = extraction_result.get("skills", [])

        # Merge with explicit skills
        for skill in explicit_skills:
            if isinstance(skill, str):
                skills.append({
                    "name": skill,
                    "category": "technical",
                    "importance": "high"
                })

        return skills

    async def _assess_candidate(
        self,
        candidate: Dict[str, Any],
        job_requirements: Dict[str, Any],
        required_skills: List[Dict],
        processor,
        ai_service
    ) -> Dict[str, Any]:
        """Assess individual candidate against requirements"""
        # Use HR processor for evaluation
        evaluation = await processor.evaluate_candidate({
            "candidate_profile": candidate,
            "job_requirements": job_requirements
        })

        # Skill matching
        skill_match = await self._match_skills(
            candidate.get("skills", []),
            required_skills,
            ai_service
        )

        # Experience assessment
        experience_score = self._calculate_experience_score(
            candidate.get("experience", []),
            job_requirements
        )

        # Culture fit (if enabled)
        culture_score = 0.7  # Default neutral
        if self.config.enable_culture_fit:
            culture_result = await ai_service.analyze(
                prompt=f"""Assess culture fit between candidate and company:
                Candidate values/style: {candidate.get('values', 'not specified')}
                Company culture: {job_requirements.get('company_culture', 'collaborative')}
                """,
                data={"candidate": candidate}
            )
            culture_score = culture_result.get("culture_fit_score", 0.7)

        # Calculate weighted overall score
        overall_score = (
            skill_match["score"] * self.config.skill_weight +
            experience_score * self.config.experience_weight +
            culture_score * self.config.culture_fit_weight
        )

        return {
            "candidate_id": candidate.get("id", "unknown"),
            "name": candidate.get("name", "Anonymous") if not self.config.anonymize_initial_screening else f"Candidate-{candidate.get('id', 'X')[:8]}",
            "overall_score": overall_score,
            "skill_score": skill_match["score"],
            "skill_details": skill_match["details"],
            "experience_score": experience_score,
            "culture_fit_score": culture_score,
            "strengths": evaluation.get("strengths", []),
            "concerns": evaluation.get("concerns", []),
            "recommendation": evaluation.get("recommendation", "review"),
            "ai_insights": evaluation.get("analysis", {})
        }

    async def _match_skills(
        self,
        candidate_skills: List[str],
        required_skills: List[Dict],
        ai_service
    ) -> Dict[str, Any]:
        """Match candidate skills against requirements"""
        if not required_skills:
            return {"score": 0.5, "details": []}

        matched = []
        total_importance = 0

        for req_skill in required_skills:
            skill_name = req_skill.get("name", req_skill) if isinstance(req_skill, dict) else req_skill
            importance = {"high": 3, "medium": 2, "low": 1}.get(
                req_skill.get("importance", "medium") if isinstance(req_skill, dict) else "medium",
                2
            )
            total_importance += importance

            # Check for direct match or synonym
            is_matched = any(
                skill_name.lower() in cs.lower() or cs.lower() in skill_name.lower()
                for cs in candidate_skills
            )

            if is_matched:
                matched.append({
                    "skill": skill_name,
                    "matched": True,
                    "importance": importance
                })
            else:
                matched.append({
                    "skill": skill_name,
                    "matched": False,
                    "importance": importance
                })

        # Calculate weighted score
        matched_importance = sum(
            m["importance"] for m in matched if m["matched"]
        )
        score = matched_importance / total_importance if total_importance > 0 else 0.5

        return {"score": score, "details": matched}

    def _calculate_experience_score(
        self,
        experience: List[Dict],
        job_requirements: Dict
    ) -> float:
        """Calculate experience relevance score"""
        required_years = job_requirements.get("min_years_experience", 0)
        preferred_years = job_requirements.get("preferred_years_experience", required_years + 2)

        # Calculate total years
        total_years = 0
        for exp in experience:
            years = exp.get("years", 1)
            if isinstance(years, str):
                try:
                    years = float(years.split("-")[0])
                except ValueError:
                    years = 1
            total_years += years

        # Score based on experience level
        if total_years >= preferred_years:
            return 1.0
        elif total_years >= required_years:
            return 0.7 + 0.3 * (total_years - required_years) / max(1, preferred_years - required_years)
        elif total_years >= required_years * 0.7:
            return 0.5 + 0.2 * (total_years / required_years)
        else:
            return max(0.3, total_years / required_years)

    def _rank_candidates(
        self,
        assessments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank candidates by overall score"""
        sorted_candidates = sorted(
            assessments,
            key=lambda x: x["overall_score"],
            reverse=True
        )

        # Add rank
        for i, candidate in enumerate(sorted_candidates, 1):
            candidate["rank"] = i
            candidate["tier"] = (
                "top" if candidate["overall_score"] >= 0.8 else
                "qualified" if candidate["overall_score"] >= 0.6 else
                "review" if candidate["overall_score"] >= 0.4 else
                "below_threshold"
            )

        return sorted_candidates

    async def _check_for_bias(
        self,
        ranked_candidates: List[Dict],
        ai_service
    ) -> Dict[str, Any]:
        """Check ranking for potential bias"""
        bias_analysis = await ai_service.analyze(
            prompt="""Analyze this candidate ranking for potential bias:
            Check for:
            - Adverse impact indicators
            - Consistent scoring across demographics
            - Fair treatment in skill assessment

            Provide bias risk score (0-1) and any concerns.
            """,
            data={"rankings": ranked_candidates[:10]}
        )

        if bias_analysis.get("bias_risk_score", 0) > 0.5:
            self.state["bias_alerts"] += 1

        return {
            "bias_risk_score": bias_analysis.get("bias_risk_score", 0.2),
            "concerns": bias_analysis.get("concerns", []),
            "recommendations": bias_analysis.get("bias_mitigation", []),
            "compliance_status": "compliant" if bias_analysis.get("bias_risk_score", 0) < 0.5 else "review_needed"
        }

    async def _generate_interview_questions(
        self,
        top_candidates: List[Dict],
        job_requirements: Dict,
        ai_service
    ) -> Dict[str, Any]:
        """Generate personalized interview questions for top candidates"""
        questions = {}

        for candidate in top_candidates:
            candidate_id = candidate.get("candidate_id", "unknown")

            # Generate questions based on gaps and strengths
            question_result = await ai_service.analyze(
                prompt=f"""Generate 5 interview questions for this candidate:
                Role: {job_requirements.get('title', 'Position')}
                Candidate Strengths: {candidate.get('strengths', [])}
                Areas to Probe: {candidate.get('concerns', [])}
                Skill Gaps: {[d['skill'] for d in candidate.get('skill_details', []) if not d.get('matched')]}

                Include mix of:
                - Behavioral questions (STAR format prompts)
                - Technical questions based on role
                - Culture fit questions
                """,
                data={"candidate": candidate, "job": job_requirements}
            )

            questions[candidate_id] = {
                "questions": question_result.get("questions", []),
                "focus_areas": question_result.get("focus_areas", []),
                "red_flags_to_watch": question_result.get("red_flags", [])
            }

        return questions


async def demo():
    """Demonstrate the Smart Recruitment Agent"""
    print("=" * 60)
    print("Smart Recruitment Agent - Demo")
    print("=" * 60)

    agent = SmartRecruitmentAgent()

    # Sample job requirements
    job = {
        "title": "Senior Software Engineer",
        "description": """
        We're looking for an experienced software engineer to join our team.
        You'll be working on distributed systems and cloud infrastructure.
        Strong problem-solving skills and team collaboration are essential.
        """,
        "required_skills": ["Python", "AWS", "Kubernetes", "SQL"],
        "preferred_skills": ["Go", "Terraform", "Redis"],
        "min_years_experience": 5,
        "preferred_years_experience": 8,
        "company_culture": "fast-paced, collaborative, innovative"
    }

    # Sample candidates
    candidates = [
        {
            "id": "cand-001",
            "name": "Alice Johnson",
            "skills": ["Python", "AWS", "Docker", "PostgreSQL", "Go"],
            "experience": [
                {"company": "TechCorp", "role": "Software Engineer", "years": 4},
                {"company": "StartupXYZ", "role": "Senior Developer", "years": 3}
            ],
            "values": "innovation, continuous learning"
        },
        {
            "id": "cand-002",
            "name": "Bob Smith",
            "skills": ["Java", "AWS", "Kubernetes", "MySQL"],
            "experience": [
                {"company": "BigCo", "role": "Backend Developer", "years": 6}
            ],
            "values": "stability, work-life balance"
        },
        {
            "id": "cand-003",
            "name": "Carol Williams",
            "skills": ["Python", "GCP", "Terraform", "Redis", "SQL"],
            "experience": [
                {"company": "CloudInc", "role": "DevOps Engineer", "years": 5},
                {"company": "DataCo", "role": "Platform Engineer", "years": 4}
            ],
            "values": "collaboration, technical excellence"
        }
    ]

    print(f"\nScreening candidates for: {job['title']}")
    print(f"Candidates: {len(candidates)}")

    try:
        result = await agent.screen_candidates(job, candidates)

        print("\n" + "-" * 40)
        print("Screening Results:")
        print("-" * 40)
        print(f"Status: {result['status']}")
        print(f"Processing Time: {result['metrics']['processing_time_seconds']:.2f}s")
        print(f"Candidates Above Threshold: {result['metrics']['candidates_above_threshold']}")

        print("\nRankings:")
        for candidate in result["ranked_candidates"]:
            print(f"  #{candidate['rank']} - {candidate['name']}")
            print(f"      Overall: {candidate['overall_score']:.2%} | Tier: {candidate['tier']}")
            print(f"      Skills: {candidate['skill_score']:.2%} | Experience: {candidate['experience_score']:.2%}")

        if result.get("bias_report"):
            print(f"\nBias Check: {result['bias_report']['compliance_status']}")

    except ImportError as e:
        print(f"\nNote: Run from project root with proper imports. Error: {e}")


if __name__ == "__main__":
    asyncio.run(demo())
