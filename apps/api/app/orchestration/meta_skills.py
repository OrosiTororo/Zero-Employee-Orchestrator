"""Meta-Skills — AI agent "learning to learn" capabilities.

Defines 5 meta-skills for AI agent self-improvement:
  - Feeling: Analyze emotional/contextual signals from user interactions
  - Seeing: Recognize patterns from past experiences
  - Dreaming: Generate creative hypothetical solutions
  - Making: Generate concrete outputs from plans
  - Learning: Extract lessons from execution results and update all meta-skills

ROADMAP v0.3: Meta-Skills foundation.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MetaSkillType(str, Enum):
    """Meta-skill type."""

    FEELING = "feeling"  # Intuition / context sensing
    SEEING = "seeing"  # Pattern recognition
    DREAMING = "dreaming"  # Creative hypothesis generation
    MAKING = "making"  # Execution / artifact generation
    LEARNING = "learning"  # Lesson extraction / self-update


@dataclass
class Insight:
    """Insight generated across meta-skills."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_skill: MetaSkillType = MetaSkillType.LEARNING
    content: str = ""
    relevance_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "id": self.id,
            "source_skill": self.source_skill.value,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat(),
            "applied_count": self.applied_count,
        }


@dataclass
class MetaSkillState:
    """Current state of each meta-skill."""

    skill_type: MetaSkillType
    confidence: float = 0.0
    experience_count: int = 0
    last_activated: datetime | None = None
    insights: list[Insight] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "skill_type": self.skill_type.value,
            "confidence": self.confidence,
            "experience_count": self.experience_count,
            "last_activated": (self.last_activated.isoformat() if self.last_activated else None),
            "insight_count": len(self.insights),
        }


# ---------------------------------------------------------------------------
# Meta-Skill Engine
# ---------------------------------------------------------------------------


class MetaSkillEngine:
    """Meta-skill engine — Unified management of 5 meta-skills.

    Coordinates the 5 elements (Feeling / Seeing / Dreaming / Making / Learning)
    to enable AI agents to improve their own learning processes.
    """

    def __init__(self) -> None:
        self._states: dict[MetaSkillType, MetaSkillState] = {
            skill_type: MetaSkillState(skill_type=skill_type) for skill_type in MetaSkillType
        }
        self._global_insights: list[Insight] = []

    # ------------------------------------------------------------------
    # Feeling — Intuition / contextual signal analysis
    # ------------------------------------------------------------------

    async def feel(self, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze emotional/contextual signals from user interaction and return intuition score.

        Args:
            context: Dict containing user speech, tone, urgency, etc.

        Returns:
            Intuition score and signal analysis results.
        """
        state = self._states[MetaSkillType.FEELING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        # Signal extraction
        urgency = context.get("urgency", 0.5)
        sentiment = context.get("sentiment", "neutral")
        complexity = context.get("complexity", 0.5)
        user_text = context.get("text", "")

        # LLM-enhanced sentiment & urgency analysis when text is available
        llm_analysis = None
        if user_text and len(user_text) > 10:
            try:
                from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

                resp = await llm_gateway.complete(
                    CompletionRequest(
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    "Analyze this user message and return JSON with "
                                    '"urgency" (0-1), "sentiment" (positive/neutral/'
                                    'negative/frustrated), "complexity" (0-1), '
                                    '"key_signals" (list of strings).\n\n'
                                    f"Message: {user_text[:500]}"
                                ),
                            }
                        ],
                        mode=ExecutionMode.SPEED,
                        temperature=0.2,
                        max_tokens=256,
                    )
                )
                import json

                content = resp.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                llm_analysis = json.loads(content)
                urgency = llm_analysis.get("urgency", urgency)
                sentiment = llm_analysis.get("sentiment", sentiment)
                complexity = llm_analysis.get("complexity", complexity)
            except Exception as exc:
                logger.debug("LLM feel analysis fallback to heuristic: %s", exc)

        # Intuition score calculation: combining urgency, complexity, and text length
        text_density = min(len(user_text) / 500.0, 1.0)
        intuition_score = urgency * 0.4 + complexity * 0.3 + text_density * 0.3

        # Sentiment mapping
        sentiment_map = {
            "positive": 0.2,
            "neutral": 0.0,
            "negative": -0.1,
            "frustrated": -0.3,
        }
        sentiment_modifier = sentiment_map.get(sentiment, 0.0)
        intuition_score = max(0.0, min(1.0, intuition_score + sentiment_modifier))

        # Update confidence based on experience
        state.confidence = min(1.0, state.confidence + 0.01 * (1.0 - state.confidence))

        result = {
            "intuition_score": round(intuition_score, 4),
            "signals": {
                "urgency": urgency,
                "sentiment": sentiment,
                "complexity": complexity,
                "text_density": round(text_density, 4),
            },
            "confidence": round(state.confidence, 4),
            "llm_enhanced": llm_analysis is not None,
        }
        if llm_analysis and "key_signals" in llm_analysis:
            result["key_signals"] = llm_analysis["key_signals"]

        logger.debug("MetaSkill FEEL: intuition=%.3f", intuition_score)
        return result

    # ------------------------------------------------------------------
    # Seeing — Pattern recognition
    # ------------------------------------------------------------------

    async def see(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recognize patterns from past experience data.

        Args:
            data: Data to analyze. Contains experiences (list of past experiences)
                  and current_context (current context).

        Returns:
            List of discovered patterns.
        """
        state = self._states[MetaSkillType.SEEING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        experiences: list[dict[str, Any]] = data.get("experiences", [])
        current_context = data.get("current_context", {})
        patterns_found: list[dict[str, Any]] = []

        # Aggregate experiences with similar context
        context_domain = current_context.get("domain", "")
        matching_experiences = [
            exp for exp in experiences if exp.get("domain", "") == context_domain
        ]

        if matching_experiences:
            # Success rate pattern
            successes = sum(1 for exp in matching_experiences if exp.get("success", False))
            total = len(matching_experiences)
            success_rate = successes / total if total > 0 else 0.0

            patterns_found.append(
                {
                    "pattern_type": "success_rate",
                    "domain": context_domain,
                    "value": round(success_rate, 4),
                    "sample_size": total,
                    "description": (
                        f"Success rate in domain '{context_domain}': "
                        f"{success_rate:.1%} ({successes}/{total})"
                    ),
                }
            )

        # Extract most frequent approaches
        approach_counts: dict[str, int] = {}
        for exp in matching_experiences:
            approach = exp.get("approach", "unknown")
            approach_counts[approach] = approach_counts.get(approach, 0) + 1

        if approach_counts:
            best_approach = max(approach_counts, key=approach_counts.get)  # type: ignore[arg-type]
            patterns_found.append(
                {
                    "pattern_type": "preferred_approach",
                    "domain": context_domain,
                    "value": best_approach,
                    "frequency": approach_counts[best_approach],
                    "description": (
                        f"Most frequent approach: '{best_approach}' ({approach_counts[best_approach]} times)"
                    ),
                }
            )

        # LLM-enhanced pattern discovery across experiences
        if len(matching_experiences) >= 3:
            try:
                import json

                from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

                exp_summaries = [
                    f"- {'SUCCESS' if e.get('success') else 'FAIL'}: "
                    f"{e.get('approach', '?')} in {e.get('domain', '?')}"
                    for e in matching_experiences[:10]
                ]
                resp = await llm_gateway.complete(
                    CompletionRequest(
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    "Analyze these past experiences and identify non-obvious patterns. "
                                    'Return JSON array of {"pattern_type": "llm_insight", '
                                    '"description": "...", "confidence": 0-1}.\n\n'
                                    "Experiences:\n" + "\n".join(exp_summaries)
                                ),
                            }
                        ],
                        mode=ExecutionMode.SPEED,
                        temperature=0.3,
                        max_tokens=256,
                    )
                )
                content = resp.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                for p in json.loads(content)[:3]:
                    p["domain"] = context_domain
                    patterns_found.append(p)
            except Exception as exc:
                logger.debug("LLM see pattern discovery fallback: %s", exc)

        # Update confidence
        state.confidence = min(
            1.0,
            state.confidence + 0.005 * len(patterns_found),
        )

        logger.debug("MetaSkill SEE: %d patterns found", len(patterns_found))
        return {
            "patterns": patterns_found,
            "total_experiences_analyzed": len(experiences),
            "matching_experiences": len(matching_experiences),
            "confidence": round(state.confidence, 4),
        }

    # ------------------------------------------------------------------
    # Dreaming — Creative hypothesis generation
    # ------------------------------------------------------------------

    async def dream(self, problem_space: dict[str, Any]) -> dict[str, Any]:
        """Generate creative hypothetical solutions from the problem space.

        Args:
            problem_space: Dict containing problem definition, constraints, known approaches, etc.

        Returns:
            List of generated hypothetical solutions.
        """
        state = self._states[MetaSkillType.DREAMING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        problem = problem_space.get("problem", "")
        constraints: list[str] = problem_space.get("constraints", [])
        known_approaches: list[str] = problem_space.get("known_approaches", [])
        goals: list[str] = problem_space.get("goals", [])

        hypotheses: list[dict[str, Any]] = []

        # Generate new solutions by combining known approaches
        if len(known_approaches) >= 2:
            for i, a1 in enumerate(known_approaches):
                for a2 in known_approaches[i + 1 :]:
                    hypotheses.append(
                        {
                            "hypothesis_id": str(uuid.uuid4()),
                            "type": "combination",
                            "description": f"Hybrid approach combining '{a1}' and '{a2}'",
                            "source_approaches": [a1, a2],
                            "novelty_score": 0.6,
                            "feasibility_score": 0.7,
                        }
                    )

        # Explore solutions via constraint relaxation
        for constraint in constraints:
            hypotheses.append(
                {
                    "hypothesis_id": str(uuid.uuid4()),
                    "type": "constraint_relaxation",
                    "description": f"Solution exploration when relaxing constraint '{constraint}'",
                    "relaxed_constraint": constraint,
                    "novelty_score": 0.8,
                    "feasibility_score": 0.4,
                }
            )

        # Stepwise solution via goal decomposition
        if goals:
            hypotheses.append(
                {
                    "hypothesis_id": str(uuid.uuid4()),
                    "type": "goal_decomposition",
                    "description": f"Stepwise approach decomposing goals into {len(goals)} stages",
                    "sub_goals": goals,
                    "novelty_score": 0.5,
                    "feasibility_score": 0.8,
                }
            )

        # LLM-enhanced creative ideation
        if problem:
            try:
                import json

                from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

                prompt = (
                    "You are a creative problem solver. Generate 2-3 novel solution "
                    "hypotheses for this problem. Return a JSON array of objects with "
                    '"description", "novelty_score" (0-1), "feasibility_score" (0-1).\n\n'
                    f"Problem: {problem[:300]}\n"
                    f"Constraints: {', '.join(constraints[:5])}\n"
                    f"Known approaches: {', '.join(known_approaches[:5])}\n"
                    "Return ONLY the JSON array."
                )
                resp = await llm_gateway.complete(
                    CompletionRequest(
                        messages=[{"role": "user", "content": prompt}],
                        mode=ExecutionMode.SPEED,
                        temperature=0.9,
                        max_tokens=512,
                    )
                )
                content = resp.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                llm_ideas = json.loads(content)
                for idea in llm_ideas[:3]:
                    hypotheses.append(
                        {
                            "hypothesis_id": str(uuid.uuid4()),
                            "type": "llm_creative",
                            "description": idea.get("description", ""),
                            "novelty_score": idea.get("novelty_score", 0.7),
                            "feasibility_score": idea.get("feasibility_score", 0.6),
                        }
                    )
            except Exception as exc:
                logger.debug("LLM dream ideation fallback to combinatorial: %s", exc)

        # Update confidence
        state.confidence = min(
            1.0,
            state.confidence + 0.008 * (1.0 - state.confidence),
        )

        logger.debug("MetaSkill DREAM: %d hypotheses generated", len(hypotheses))
        return {
            "hypotheses": hypotheses,
            "problem_summary": problem[:200],
            "constraints_count": len(constraints),
            "confidence": round(state.confidence, 4),
        }

    # ------------------------------------------------------------------
    # Making — Plan execution / artifact generation
    # ------------------------------------------------------------------

    async def make(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Generate concrete outputs from a plan.

        Args:
            plan: Plan to execute. Contains steps, resources, expected_output.

        Returns:
            Execution results and status.
        """
        state = self._states[MetaSkillType.MAKING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        steps: list[dict[str, Any]] = plan.get("steps", [])
        resources: list[str] = plan.get("resources", [])
        expected_output = plan.get("expected_output", "")

        execution_results: list[dict[str, Any]] = []
        completed = 0
        failed = 0

        for i, step in enumerate(steps):
            step_name = step.get("name", f"step_{i + 1}")
            step_action = step.get("action", "")
            prerequisites = step.get("prerequisites", [])

            # Prerequisite check
            prereqs_met = all(
                any(r["step"] == p and r["success"] for r in execution_results)
                for p in prerequisites
            )

            if not prereqs_met and prerequisites:
                execution_results.append(
                    {
                        "step": step_name,
                        "action": step_action,
                        "success": False,
                        "reason": "Prerequisites not met",
                        "order": i + 1,
                    }
                )
                failed += 1
                continue

            # Step execution — LLM-assisted when action is meaningful
            step_output = "Execution completed"
            step_success = True
            if step_action and len(step_action) > 5:
                try:
                    from app.providers.gateway import (
                        CompletionRequest,
                        ExecutionMode,
                        llm_gateway,
                    )

                    resp = await llm_gateway.complete(
                        CompletionRequest(
                            messages=[
                                {
                                    "role": "user",
                                    "content": (
                                        f"Execute this step and return the result.\n"
                                        f"Step: {step_name}\nAction: {step_action[:300]}\n"
                                        f"Expected output: {expected_output[:200]}"
                                    ),
                                }
                            ],
                            mode=ExecutionMode.SPEED,
                            temperature=0.5,
                            max_tokens=512,
                        )
                    )
                    if resp.content:
                        step_output = resp.content[:500]
                        step_success = True
                    else:
                        step_output = "LLM returned empty response"
                        step_success = False
                except Exception as exc:
                    logger.debug("LLM make step fallback to simulated: %s", exc)
                    step_output = f"Execution simulated (LLM unavailable): {step_action[:100]}"
                    step_success = False

            execution_results.append(
                {
                    "step": step_name,
                    "action": step_action,
                    "success": step_success,
                    "reason": step_output,
                    "order": i + 1,
                }
            )
            completed += 1

        total = len(steps)
        completion_rate = completed / total if total > 0 else 0.0

        # Update confidence
        state.confidence = min(
            1.0,
            state.confidence + 0.01 * completion_rate,
        )

        logger.debug("MetaSkill MAKE: %d/%d steps completed", completed, total)
        return {
            "execution_results": execution_results,
            "completed": completed,
            "failed": failed,
            "total_steps": total,
            "completion_rate": round(completion_rate, 4),
            "expected_output": expected_output,
            "resources_used": resources,
            "confidence": round(state.confidence, 4),
        }

    # ------------------------------------------------------------------
    # Learning — Lesson extraction / self-update
    # ------------------------------------------------------------------

    async def learn(self, outcome: dict[str, Any]) -> dict[str, Any]:
        """Extract lessons from execution results and update all meta-skill states.

        Args:
            outcome: Execution result. Contains success, domain, approach, details, feedback.

        Returns:
            Extracted lessons and updated meta-skill states.
        """
        state = self._states[MetaSkillType.LEARNING]
        state.experience_count += 1
        state.last_activated = datetime.now(UTC)

        success = outcome.get("success", False)
        domain = outcome.get("domain", "general")
        approach = outcome.get("approach", "")
        details = outcome.get("details", "")
        feedback = outcome.get("feedback", "")

        lessons: list[dict[str, Any]] = []

        # Extract lessons from success/failure
        if success:
            lesson = {
                "type": "success_pattern",
                "domain": domain,
                "approach": approach,
                "description": f"'{approach}' succeeded in domain '{domain}'",
                "actionable": f"Consider '{approach}' as priority in similar situations",
            }
            lessons.append(lesson)
        else:
            lesson = {
                "type": "failure_pattern",
                "domain": domain,
                "approach": approach,
                "description": f"'{approach}' failed in domain '{domain}': {details[:100]}",
                "actionable": f"Reconsider application conditions for '{approach}'",
            }
            lessons.append(lesson)

        # Lessons from feedback
        if feedback:
            lessons.append(
                {
                    "type": "feedback_insight",
                    "domain": domain,
                    "description": f"User feedback: {feedback[:200]}",
                    "actionable": "Adjust approach based on feedback",
                }
            )

        # LLM-enhanced lesson synthesis
        if details or feedback:
            try:
                import json

                from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

                synthesis_prompt = (
                    "Analyze this task outcome and extract 1-2 actionable lessons. "
                    'Return JSON array of {"type", "description", "actionable"}.\n\n'
                    f"Domain: {domain}\nApproach: {approach}\n"
                    f"Success: {success}\nDetails: {details[:300]}\n"
                    f"Feedback: {feedback[:200]}"
                )
                resp = await llm_gateway.complete(
                    CompletionRequest(
                        messages=[{"role": "user", "content": synthesis_prompt}],
                        mode=ExecutionMode.SPEED,
                        temperature=0.3,
                        max_tokens=256,
                    )
                )
                content = resp.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                llm_lessons = json.loads(content)
                for ll in llm_lessons[:2]:
                    ll["domain"] = domain
                    ll["llm_synthesized"] = True
                    lessons.append(ll)
            except Exception as exc:
                logger.debug("LLM learn synthesis fallback: %s", exc)

        # Generate and store insights
        for lesson in lessons:
            insight = Insight(
                source_skill=MetaSkillType.LEARNING,
                content=lesson.get("description", ""),
                relevance_score=0.8 if success else 0.6,
            )
            state.insights.append(insight)
            self._global_insights.append(insight)

        # Fine-tune confidence of all meta-skills
        confidence_delta = 0.005 if success else -0.002
        for skill_state in self._states.values():
            skill_state.confidence = max(
                0.0,
                min(1.0, skill_state.confidence + confidence_delta),
            )

        logger.info(
            "MetaSkill LEARN: %d lessons extracted (success=%s)",
            len(lessons),
            success,
        )
        return {
            "lessons": lessons,
            "insights_generated": len(lessons),
            "success": success,
            "all_states": {k.value: v.to_dict() for k, v in self._states.items()},
        }

    # ------------------------------------------------------------------
    # State retrieval
    # ------------------------------------------------------------------

    def get_state(self, skill_type: MetaSkillType) -> MetaSkillState:
        """Return current state of the specified meta-skill."""
        return self._states[skill_type]

    def get_all_states(self) -> dict[MetaSkillType, MetaSkillState]:
        """Return states of all meta-skills."""
        return dict(self._states)

    # ------------------------------------------------------------------
    # Cross-cutting insights
    # ------------------------------------------------------------------

    async def generate_meta_insight(self) -> Insight | None:
        """Generate an integrated insight across all meta-skills.

        Synthesizes each skill's experience, confidence, and recent insights
        to derive a meta-level insight.
        """
        active_skills = [s for s in self._states.values() if s.experience_count > 0]
        if not active_skills:
            return None

        # Identify most experienced skill and weakest skill
        most_experienced = max(active_skills, key=lambda s: s.experience_count)
        least_confident = min(active_skills, key=lambda s: s.confidence)

        # Extract themes from recent insights
        recent_insights = sorted(
            self._global_insights,
            key=lambda i: i.created_at,
            reverse=True,
        )[:10]

        insight_summary = (
            "; ".join(i.content[:50] for i in recent_insights) if recent_insights else "No insights"
        )

        # Build context for LLM synthesis
        context = (
            f"Meta-analysis context:\n"
            f"- Most utilized skill: '{most_experienced.skill_type.value}' "
            f"(experience count: {most_experienced.experience_count}, "
            f"confidence: {most_experienced.confidence:.2f})\n"
            f"- Lowest confidence skill: '{least_confident.skill_type.value}' "
            f"(confidence: {least_confident.confidence:.2f})\n"
            f"- Recent insights: {insight_summary}\n"
            f"- Total active skills: {len(active_skills)}"
        )

        content = context  # fallback
        try:
            from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

            resp = await llm_gateway.complete(
                CompletionRequest(
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                f"Synthesize the following AI meta-skill data into a concise "
                                f"actionable insight (1-2 sentences):\n\n{context}"
                            ),
                        }
                    ],
                    mode=ExecutionMode.SPEED,
                    temperature=0.4,
                    max_tokens=200,
                )
            )
            if resp.content:
                content = resp.content[:400]
        except Exception as exc:
            logger.debug("generate_meta_insight LLM fallback: %s", exc)

        meta_insight = Insight(
            source_skill=MetaSkillType.LEARNING,
            content=content,
            relevance_score=0.9,
        )
        self._global_insights.append(meta_insight)

        logger.info("Meta-insight generated: %s", content[:80])
        return meta_insight

    async def suggest_learning_path(self, weakness_area: str) -> dict[str, Any]:
        """Suggest a learning path for a weakness area.

        Args:
            weakness_area: Area to improve (e.g., "pattern_recognition",
                "creative_thinking").

        Returns:
            Recommended learning steps and meta-skill utilization order.
        """
        # Mapping weakness areas to meta-skills
        area_skill_map: dict[str, list[MetaSkillType]] = {
            "pattern_recognition": [
                MetaSkillType.SEEING,
                MetaSkillType.LEARNING,
            ],
            "creative_thinking": [
                MetaSkillType.DREAMING,
                MetaSkillType.FEELING,
            ],
            "execution": [
                MetaSkillType.MAKING,
                MetaSkillType.SEEING,
            ],
            "user_understanding": [
                MetaSkillType.FEELING,
                MetaSkillType.LEARNING,
            ],
            "self_improvement": [
                MetaSkillType.LEARNING,
                MetaSkillType.DREAMING,
            ],
        }

        relevant_skills = area_skill_map.get(
            weakness_area,
            list(MetaSkillType),
        )

        steps: list[dict[str, Any]] = []
        for i, skill_type in enumerate(relevant_skills):
            skill_state = self._states[skill_type]
            steps.append(
                {
                    "order": i + 1,
                    "skill": skill_type.value,
                    "current_confidence": round(skill_state.confidence, 4),
                    "experience_count": skill_state.experience_count,
                    "recommendation": (
                        f"Strengthen '{skill_type.value}' skill: "
                        f"current confidence {skill_state.confidence:.2f}, "
                        f"experience count {skill_state.experience_count}"
                    ),
                    "exercises": self._suggest_exercises(skill_type),
                }
            )

        return {
            "weakness_area": weakness_area,
            "learning_path": steps,
            "estimated_sessions": max(3, 10 - len(relevant_skills)),
            "priority_skill": relevant_skills[0].value if relevant_skills else None,
        }

    def _suggest_exercises(self, skill_type: MetaSkillType) -> list[str]:
        """Suggest practice exercises for each meta-skill."""
        exercises_map: dict[MetaSkillType, list[str]] = {
            MetaSkillType.FEELING: [
                "Perform tone analysis on 10 user utterances",
                "Measure intuition accuracy during context switches",
            ],
            MetaSkillType.SEEING: [
                "Extract patterns from 50 past execution logs",
                "Compare and analyze success factors of similar tasks",
            ],
            MetaSkillType.DREAMING: [
                "Generate 5 new solutions from combinations of known approaches",
                "Explore 3 constraint relaxation scenarios",
            ],
            MetaSkillType.MAKING: [
                "Execute 3 small-scale plans and measure completion rate",
                "Verify accuracy of prerequisite chains",
            ],
            MetaSkillType.LEARNING: [
                "Extract lessons from 10 recent successes/failures",
                "Identify improvement points in the feedback loop",
            ],
        }
        return exercises_map.get(skill_type, [])


# Global instance
meta_skill_engine = MetaSkillEngine()
