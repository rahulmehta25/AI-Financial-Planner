"""
Habit Formation System with BJ Fogg Model Implementation

Implements behavior change through tiny habits, motivation curves,
and ability mapping with gamification elements.
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from dataclasses import dataclass, field
import uuid

import numpy as np
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.base import SessionLocal
from app.models.user import User
from app.ai.llm_client import LLMClientManager
from app.services.notifications.manager import NotificationManager

logger = logging.getLogger(__name__)


class HabitType(str, Enum):
    """Types of financial habits."""
    DAILY_TRACKING = "daily_tracking"
    WEEKLY_REVIEW = "weekly_review"
    MONTHLY_BUDGET = "monthly_budget"
    SAVING_TRANSFER = "saving_transfer"
    INVESTMENT_CONTRIBUTION = "investment_contribution"
    EXPENSE_LOGGING = "expense_logging"
    GOAL_CHECK = "goal_check"
    LEARNING_SESSION = "learning_session"
    SPENDING_PAUSE = "spending_pause"
    DEBT_PAYMENT = "debt_payment"
    FINANCIAL_PLANNING = "financial_planning"
    MINDFUL_SPENDING = "mindful_spending"


class HabitStatus(str, Enum):
    """Status of habit formation."""
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class HabitDifficulty(str, Enum):
    """Difficulty levels for habits."""
    TINY = "tiny"  # < 2 minutes
    EASY = "easy"  # 2-5 minutes
    MODERATE = "moderate"  # 5-15 minutes
    CHALLENGING = "challenging"  # 15-30 minutes
    HARD = "hard"  # > 30 minutes


class RewardType(str, Enum):
    """Types of rewards for habit completion."""
    BADGE = "badge"
    POINTS = "points"
    STREAK_BONUS = "streak_bonus"
    MILESTONE = "milestone"
    ACHIEVEMENT = "achievement"
    LEVEL_UP = "level_up"
    UNLOCK_FEATURE = "unlock_feature"


@dataclass
class HabitTrigger:
    """Represents a habit trigger (BJ Fogg model)."""
    trigger_type: str  # time, location, action, emotional
    description: str
    specific_time: Optional[datetime] = None
    existing_habit: Optional[str] = None  # For habit stacking
    reminder_enabled: bool = True
    notification_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HabitMetrics:
    """Metrics for tracking habit performance."""
    total_completions: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    completion_rate: float = 0.0
    average_completion_time: float = 0.0
    last_completed: Optional[datetime] = None
    total_points_earned: int = 0
    badges_earned: List[str] = field(default_factory=list)
    difficulty_progression: List[str] = field(default_factory=list)


@dataclass
class FinancialHabit:
    """Represents a financial habit."""
    habit_id: str
    user_id: str
    habit_type: HabitType
    name: str
    description: str
    target_behavior: str
    current_behavior: Optional[str]
    difficulty: HabitDifficulty
    status: HabitStatus
    trigger: HabitTrigger
    frequency: str  # daily, weekly, monthly
    duration_minutes: int
    start_date: datetime
    target_date: Optional[datetime]
    metrics: HabitMetrics
    rewards: List[Dict[str, Any]]
    motivation_level: float  # 0-1
    ability_level: float  # 0-1
    prompt_effectiveness: float  # 0-1
    habit_stack: Optional[List[str]] = None
    celebration_ritual: Optional[str] = None
    accountability_partner: Optional[str] = None
    notes: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class HabitFormationPlan(BaseModel):
    """Plan for forming a new habit."""
    habit_type: HabitType
    tiny_version: str
    scaled_versions: List[str]
    trigger_options: List[Dict[str, Any]]
    celebration_ideas: List[str]
    potential_obstacles: List[str]
    solutions: Dict[str, str]
    success_metrics: Dict[str, Any]
    timeline: Dict[str, Any]


class BehaviorGrid(BaseModel):
    """BJ Fogg Behavior Grid mapping."""
    behavior_type: str  # dot, span, path
    duration: str  # one_time, period, permanent
    motivation_required: float
    ability_required: float
    trigger_type: str
    examples: List[str]


class HabitFormationSystem:
    """System for building and tracking financial habits using behavioral science."""
    
    def __init__(self, llm_manager: LLMClientManager, notification_manager: NotificationManager):
        self.llm_manager = llm_manager
        self.notification_manager = notification_manager
        
        # Habit storage
        self.active_habits: Dict[str, List[FinancialHabit]] = {}
        
        # BJ Fogg model components
        self.behavior_map = self._initialize_behavior_map()
        self.tiny_habits_library = self._initialize_tiny_habits()
        self.celebration_library = self._initialize_celebrations()
        
        # Gamification elements
        self.badge_system = self._initialize_badge_system()
        self.level_system = self._initialize_level_system()
        
        # Habit stacking templates
        self.habit_stacks = self._initialize_habit_stacks()
    
    async def create_habit_plan(
        self,
        user_id: str,
        desired_outcome: str,
        current_behavior: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> HabitFormationPlan:
        """Create a personalized habit formation plan."""
        
        try:
            # Analyze user's request
            analysis = await self._analyze_habit_request(
                desired_outcome, current_behavior, constraints
            )
            
            # Identify appropriate habit type
            habit_type = self._identify_habit_type(analysis)
            
            # Generate tiny habit version
            tiny_habit = await self._generate_tiny_habit(
                habit_type, desired_outcome, constraints
            )
            
            # Create scaled versions for progression
            scaled_versions = await self._create_scaled_versions(tiny_habit)
            
            # Identify optimal triggers
            triggers = await self._identify_triggers(user_id, habit_type)
            
            # Generate celebration ideas
            celebrations = await self._generate_celebrations(user_id, habit_type)
            
            # Identify obstacles and solutions
            obstacles_solutions = await self._identify_obstacles_and_solutions(
                user_id, habit_type, desired_outcome
            )
            
            # Define success metrics and timeline
            metrics = self._define_success_metrics(habit_type)
            timeline = self._create_timeline(habit_type, constraints)
            
            return HabitFormationPlan(
                habit_type=habit_type,
                tiny_version=tiny_habit,
                scaled_versions=scaled_versions,
                trigger_options=triggers,
                celebration_ideas=celebrations,
                potential_obstacles=obstacles_solutions['obstacles'],
                solutions=obstacles_solutions['solutions'],
                success_metrics=metrics,
                timeline=timeline
            )
            
        except Exception as e:
            logger.error(f"Error creating habit plan: {str(e)}")
            return self._get_fallback_habit_plan(desired_outcome)
    
    async def start_habit(
        self,
        user_id: str,
        habit_plan: HabitFormationPlan,
        selected_trigger: Dict[str, Any],
        selected_celebration: str
    ) -> FinancialHabit:
        """Start tracking a new habit."""
        
        try:
            # Create habit trigger
            trigger = HabitTrigger(
                trigger_type=selected_trigger['type'],
                description=selected_trigger['description'],
                specific_time=selected_trigger.get('time'),
                existing_habit=selected_trigger.get('existing_habit'),
                reminder_enabled=True,
                notification_settings={'frequency': 'daily', 'time': '09:00'}
            )
            
            # Initialize habit
            habit = FinancialHabit(
                habit_id=str(uuid.uuid4()),
                user_id=user_id,
                habit_type=habit_plan.habit_type,
                name=f"{habit_plan.habit_type.value.replace('_', ' ').title()}",
                description=habit_plan.tiny_version,
                target_behavior=habit_plan.scaled_versions[-1],  # Ultimate goal
                current_behavior=habit_plan.tiny_version,  # Start tiny
                difficulty=HabitDifficulty.TINY,
                status=HabitStatus.ACTIVE,
                trigger=trigger,
                frequency=self._determine_frequency(habit_plan.habit_type),
                duration_minutes=2,  # Start with tiny duration
                start_date=datetime.utcnow(),
                target_date=datetime.utcnow() + timedelta(days=66),  # 66 days to form habit
                metrics=HabitMetrics(),
                rewards=[],
                motivation_level=0.7,
                ability_level=0.9,  # High ability for tiny habits
                prompt_effectiveness=0.8,
                celebration_ritual=selected_celebration,
                notes=[]
            )
            
            # Store habit
            if user_id not in self.active_habits:
                self.active_habits[user_id] = []
            self.active_habits[user_id].append(habit)
            
            # Schedule reminders
            await self._schedule_habit_reminders(habit)
            
            # Log habit start
            await self._log_habit_event(habit, "started")
            
            return habit
            
        except Exception as e:
            logger.error(f"Error starting habit: {str(e)}")
            raise
    
    async def record_habit_completion(
        self,
        user_id: str,
        habit_id: str,
        completion_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record habit completion and provide feedback."""
        
        try:
            # Find habit
            habit = self._find_habit(user_id, habit_id)
            if not habit:
                raise ValueError(f"Habit {habit_id} not found")
            
            # Update metrics
            habit.metrics.total_completions += 1
            habit.metrics.current_streak += 1
            habit.metrics.longest_streak = max(
                habit.metrics.longest_streak,
                habit.metrics.current_streak
            )
            habit.metrics.last_completed = datetime.utcnow()
            
            # Calculate completion rate
            days_active = (datetime.utcnow() - habit.start_date).days + 1
            habit.metrics.completion_rate = habit.metrics.total_completions / days_active
            
            # Award points and badges
            rewards = await self._calculate_rewards(habit, completion_data)
            habit.rewards.extend(rewards)
            
            # Check for level up opportunity
            level_up = await self._check_level_progression(habit)
            
            # Generate celebration message
            celebration = await self._generate_celebration_message(habit, rewards)
            
            # Update behavior model (MAB - Motivation, Ability, Behavior)
            await self._update_behavior_model(habit, completion_data)
            
            # Check if ready to scale up
            scale_up = await self._check_scale_readiness(habit)
            
            # Provide next action
            next_action = await self._suggest_next_action(habit, scale_up)
            
            return {
                'success': True,
                'streak': habit.metrics.current_streak,
                'rewards': rewards,
                'celebration': celebration,
                'level_up': level_up,
                'scale_up': scale_up,
                'next_action': next_action,
                'progress': {
                    'completion_rate': habit.metrics.completion_rate,
                    'days_active': days_active,
                    'total_completions': habit.metrics.total_completions
                }
            }
            
        except Exception as e:
            logger.error(f"Error recording completion: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_habit_insights(
        self,
        user_id: str,
        habit_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get insights about habit formation progress."""
        
        try:
            if habit_id:
                habit = self._find_habit(user_id, habit_id)
                if not habit:
                    raise ValueError(f"Habit {habit_id} not found")
                habits = [habit]
            else:
                habits = self.active_habits.get(user_id, [])
            
            insights = {
                'summary': await self._generate_habit_summary(habits),
                'streaks': self._analyze_streaks(habits),
                'completion_patterns': await self._analyze_completion_patterns(habits),
                'obstacles_encountered': await self._identify_encountered_obstacles(habits),
                'recommendations': await self._generate_habit_recommendations(habits),
                'celebration_stats': self._analyze_celebration_effectiveness(habits),
                'behavior_change_progress': await self._assess_behavior_change(habits)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting habit insights: {str(e)}")
            return {'error': str(e)}
    
    async def suggest_habit_stack(
        self,
        user_id: str,
        new_habit_type: HabitType
    ) -> List[Dict[str, Any]]:
        """Suggest existing habits to stack new habit with."""
        
        try:
            user_habits = self.active_habits.get(user_id, [])
            
            # Find compatible habits for stacking
            compatible_habits = []
            for habit in user_habits:
                if habit.status == HabitStatus.ACTIVE and habit.metrics.completion_rate > 0.8:
                    compatibility = await self._assess_stacking_compatibility(
                        habit, new_habit_type
                    )
                    if compatibility > 0.7:
                        compatible_habits.append({
                            'existing_habit': habit.name,
                            'existing_trigger': habit.trigger.description,
                            'compatibility_score': compatibility,
                            'suggested_sequence': await self._suggest_stack_sequence(
                                habit, new_habit_type
                            ),
                            'benefits': await self._explain_stack_benefits(
                                habit, new_habit_type
                            )
                        })
            
            # Sort by compatibility
            compatible_habits.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return compatible_habits[:3]  # Top 3 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting habit stack: {str(e)}")
            return []
    
    async def pause_habit(
        self,
        user_id: str,
        habit_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pause a habit temporarily."""
        
        try:
            habit = self._find_habit(user_id, habit_id)
            if not habit:
                raise ValueError(f"Habit {habit_id} not found")
            
            habit.status = HabitStatus.PAUSED
            habit.notes.append({
                'type': 'paused',
                'timestamp': datetime.utcnow().isoformat(),
                'reason': reason or 'User requested pause'
            })
            
            # Cancel reminders
            await self._cancel_habit_reminders(habit)
            
            # Provide resumption plan
            resumption_plan = await self._create_resumption_plan(habit, reason)
            
            return {
                'success': True,
                'habit_id': habit_id,
                'resumption_plan': resumption_plan,
                'streak_preserved': habit.metrics.current_streak > 0
            }
            
        except Exception as e:
            logger.error(f"Error pausing habit: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def resume_habit(
        self,
        user_id: str,
        habit_id: str,
        adjustments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resume a paused habit with optional adjustments."""
        
        try:
            habit = self._find_habit(user_id, habit_id)
            if not habit:
                raise ValueError(f"Habit {habit_id} not found")
            
            # Apply adjustments if provided
            if adjustments:
                await self._apply_habit_adjustments(habit, adjustments)
            
            habit.status = HabitStatus.ACTIVE
            habit.notes.append({
                'type': 'resumed',
                'timestamp': datetime.utcnow().isoformat(),
                'adjustments': adjustments
            })
            
            # Reschedule reminders
            await self._schedule_habit_reminders(habit)
            
            # Provide encouragement and tips
            encouragement = await self._generate_resumption_encouragement(habit)
            
            return {
                'success': True,
                'habit_id': habit_id,
                'encouragement': encouragement,
                'current_streak': habit.metrics.current_streak
            }
            
        except Exception as e:
            logger.error(f"Error resuming habit: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _analyze_habit_request(
        self,
        desired_outcome: str,
        current_behavior: Optional[str],
        constraints: Optional[Dict]
    ) -> Dict[str, Any]:
        """Analyze user's habit formation request."""
        
        prompt = f"""
        Analyze this habit formation request:
        
        Desired Outcome: {desired_outcome}
        Current Behavior: {current_behavior or 'Not specified'}
        Constraints: {json.dumps(constraints) if constraints else 'None'}
        
        Identify:
        1. Core behavior change needed
        2. Motivation level required (1-10)
        3. Ability level required (1-10)
        4. Best habit category
        5. Potential challenges
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response (simplified for example)
            return {
                'core_behavior': desired_outcome,
                'motivation_required': 5,
                'ability_required': 3,
                'category': 'savings',
                'challenges': ['consistency', 'remembering']
            }
        except:
            return {
                'core_behavior': desired_outcome,
                'motivation_required': 5,
                'ability_required': 5,
                'category': 'general',
                'challenges': []
            }
    
    def _identify_habit_type(self, analysis: Dict[str, Any]) -> HabitType:
        """Identify appropriate habit type from analysis."""
        
        category = analysis.get('category', '').lower()
        
        type_mapping = {
            'tracking': HabitType.DAILY_TRACKING,
            'saving': HabitType.SAVING_TRANSFER,
            'budget': HabitType.MONTHLY_BUDGET,
            'investment': HabitType.INVESTMENT_CONTRIBUTION,
            'expense': HabitType.EXPENSE_LOGGING,
            'debt': HabitType.DEBT_PAYMENT,
            'review': HabitType.WEEKLY_REVIEW,
            'learning': HabitType.LEARNING_SESSION
        }
        
        for key, habit_type in type_mapping.items():
            if key in category:
                return habit_type
        
        return HabitType.DAILY_TRACKING  # Default
    
    async def _generate_tiny_habit(
        self,
        habit_type: HabitType,
        desired_outcome: str,
        constraints: Optional[Dict]
    ) -> str:
        """Generate tiny version of habit (< 2 minutes)."""
        
        # Use predefined tiny habits
        tiny_habits = self.tiny_habits_library.get(habit_type, {})
        
        if tiny_habits:
            return tiny_habits.get('starter', f"Spend 1 minute on {habit_type.value}")
        
        # Generate with AI if not in library
        prompt = f"""
        Create a tiny habit (< 2 minutes) for:
        Habit Type: {habit_type.value}
        Goal: {desired_outcome}
        
        Make it so easy that it's almost impossible to fail.
        Example: "Check bank balance" instead of "Complete full budget review"
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=100
            )
            return response.content.strip()
        except:
            return f"Spend 1 minute on {habit_type.value.replace('_', ' ')}"
    
    async def _create_scaled_versions(self, tiny_habit: str) -> List[str]:
        """Create progressively scaled versions of habit."""
        
        return [
            tiny_habit,  # Tiny (< 2 min)
            f"{tiny_habit} for 5 minutes",  # Easy
            f"{tiny_habit} and take one action",  # Moderate
            f"Complete full {tiny_habit} routine",  # Challenging
            f"Master level: {tiny_habit} with optimization"  # Hard
        ]
    
    async def _identify_triggers(
        self,
        user_id: str,
        habit_type: HabitType
    ) -> List[Dict[str, Any]]:
        """Identify optimal triggers for habit."""
        
        triggers = [
            {
                'type': 'time',
                'description': 'Every morning with coffee',
                'time': '07:00',
                'effectiveness': 0.85
            },
            {
                'type': 'action',
                'description': 'After checking email',
                'existing_habit': 'email_check',
                'effectiveness': 0.75
            },
            {
                'type': 'location',
                'description': 'When arriving at work',
                'effectiveness': 0.70
            }
        ]
        
        return triggers
    
    async def _generate_celebrations(
        self,
        user_id: str,
        habit_type: HabitType
    ) -> List[str]:
        """Generate celebration ideas for habit completion."""
        
        base_celebrations = self.celebration_library.get('universal', [])
        type_specific = self.celebration_library.get(habit_type.value, [])
        
        return base_celebrations + type_specific
    
    async def _identify_obstacles_and_solutions(
        self,
        user_id: str,
        habit_type: HabitType,
        desired_outcome: str
    ) -> Dict[str, Any]:
        """Identify potential obstacles and solutions."""
        
        common_obstacles = {
            'forgetting': 'Set multiple reminders and visual cues',
            'lack_of_time': 'Start with 1-minute version',
            'low_motivation': 'Focus on tiny wins and celebrations',
            'complexity': 'Simplify to smallest possible action',
            'inconsistent_schedule': 'Link to existing stable habit'
        }
        
        return {
            'obstacles': list(common_obstacles.keys())[:3],
            'solutions': common_obstacles
        }
    
    def _define_success_metrics(self, habit_type: HabitType) -> Dict[str, Any]:
        """Define success metrics for habit."""
        
        return {
            'consistency': {'target': 0.8, 'measurement': 'completion_rate'},
            'streak': {'target': 7, 'measurement': 'consecutive_days'},
            'progression': {'target': 3, 'measurement': 'difficulty_levels'},
            'time_to_habit': {'target': 66, 'measurement': 'days'},
            'automation': {'target': 0.9, 'measurement': 'unprompted_completions'}
        }
    
    def _create_timeline(
        self,
        habit_type: HabitType,
        constraints: Optional[Dict]
    ) -> Dict[str, Any]:
        """Create habit formation timeline."""
        
        return {
            'week_1_2': 'Establish tiny habit with celebration',
            'week_3_4': 'Increase consistency to daily',
            'week_5_6': 'Scale up difficulty slightly',
            'week_7_8': 'Solidify routine and reduce prompts',
            'week_9_10': 'Full habit integration',
            'maintenance': 'Continue with periodic challenges'
        }
    
    def _find_habit(self, user_id: str, habit_id: str) -> Optional[FinancialHabit]:
        """Find a specific habit."""
        
        habits = self.active_habits.get(user_id, [])
        for habit in habits:
            if habit.habit_id == habit_id:
                return habit
        return None
    
    async def _calculate_rewards(
        self,
        habit: FinancialHabit,
        completion_data: Dict
    ) -> List[Dict[str, Any]]:
        """Calculate rewards for habit completion."""
        
        rewards = []
        
        # Base points
        points = 10
        
        # Streak bonuses
        if habit.metrics.current_streak == 7:
            rewards.append({'type': RewardType.STREAK_BONUS, 'value': 50, 'name': 'Week Warrior'})
            points += 50
        elif habit.metrics.current_streak == 30:
            rewards.append({'type': RewardType.STREAK_BONUS, 'value': 200, 'name': 'Monthly Master'})
            points += 200
        elif habit.metrics.current_streak == 100:
            rewards.append({'type': RewardType.ACHIEVEMENT, 'value': 1000, 'name': 'Century Club'})
            points += 1000
        
        # Consistency rewards
        if habit.metrics.completion_rate >= 0.9 and habit.metrics.total_completions >= 20:
            rewards.append({'type': RewardType.BADGE, 'value': 1, 'name': 'Consistency Champion'})
        
        # Difficulty progression rewards
        if completion_data.get('scaled_up', False):
            rewards.append({'type': RewardType.LEVEL_UP, 'value': 1, 'name': 'Level Up!'})
            points += 25
        
        rewards.append({'type': RewardType.POINTS, 'value': points, 'name': 'Completion Points'})
        
        # Update total points
        habit.metrics.total_points_earned += points
        
        return rewards
    
    async def _check_level_progression(self, habit: FinancialHabit) -> Optional[Dict]:
        """Check if habit should progress to next level."""
        
        if habit.metrics.completion_rate >= 0.9 and habit.metrics.current_streak >= 7:
            if habit.difficulty == HabitDifficulty.TINY:
                return {'new_level': HabitDifficulty.EASY, 'unlocked': 'Extended habit time'}
            elif habit.difficulty == HabitDifficulty.EASY:
                return {'new_level': HabitDifficulty.MODERATE, 'unlocked': 'Advanced techniques'}
        
        return None
    
    async def _generate_celebration_message(
        self,
        habit: FinancialHabit,
        rewards: List[Dict]
    ) -> str:
        """Generate personalized celebration message."""
        
        messages = [
            f"Fantastic! You've completed {habit.name} for {habit.metrics.current_streak} days straight!",
            f"Your consistency is paying off with a {habit.metrics.completion_rate:.0%} success rate!",
            f"You earned {sum(r['value'] for r in rewards if r['type'] == RewardType.POINTS)} points today!"
        ]
        
        if any(r['type'] == RewardType.STREAK_BONUS for r in rewards):
            messages.append("Streak bonus unlocked! Keep the momentum going!")
        
        return " ".join(messages[:2])
    
    async def _update_behavior_model(
        self,
        habit: FinancialHabit,
        completion_data: Dict
    ) -> None:
        """Update MAB (Motivation, Ability, Behavior) model."""
        
        # Update ability based on completion time
        if completion_data.get('completion_time', 0) < habit.duration_minutes:
            habit.ability_level = min(1.0, habit.ability_level + 0.02)
        
        # Update motivation based on streak
        if habit.metrics.current_streak > 0:
            habit.motivation_level = min(1.0, habit.motivation_level + 0.01)
        
        # Update prompt effectiveness
        if completion_data.get('needed_reminder', True):
            habit.prompt_effectiveness *= 0.98
        else:
            habit.prompt_effectiveness = min(1.0, habit.prompt_effectiveness * 1.02)
    
    async def _check_scale_readiness(self, habit: FinancialHabit) -> bool:
        """Check if habit is ready to scale up."""
        
        return (
            habit.metrics.completion_rate >= 0.9 and
            habit.metrics.current_streak >= 7 and
            habit.ability_level >= 0.8
        )
    
    async def _suggest_next_action(
        self,
        habit: FinancialHabit,
        scale_up: bool
    ) -> str:
        """Suggest next action for habit development."""
        
        if scale_up:
            return f"You're ready to level up! Try extending {habit.name} by 2 minutes tomorrow."
        elif habit.metrics.current_streak < 3:
            return "Focus on building consistency. Every completion counts!"
        elif habit.metrics.completion_rate < 0.7:
            return "Try setting an additional reminder or simplifying the habit further."
        else:
            return f"Keep going! You're building a strong {habit.name} habit."
    
    async def _schedule_habit_reminders(self, habit: FinancialHabit) -> None:
        """Schedule reminders for habit."""
        
        if habit.trigger.reminder_enabled:
            # Schedule daily reminder
            await self.notification_manager.schedule_notification(
                user_id=habit.user_id,
                notification_type='habit_reminder',
                content={
                    'habit_name': habit.name,
                    'habit_id': habit.habit_id,
                    'trigger': habit.trigger.description,
                    'celebration': habit.celebration_ritual
                },
                scheduled_time=habit.trigger.specific_time or datetime.utcnow() + timedelta(hours=9)
            )
    
    async def _cancel_habit_reminders(self, habit: FinancialHabit) -> None:
        """Cancel scheduled reminders for habit."""
        
        await self.notification_manager.cancel_scheduled_notifications(
            user_id=habit.user_id,
            notification_type='habit_reminder',
            reference_id=habit.habit_id
        )
    
    async def _log_habit_event(self, habit: FinancialHabit, event_type: str) -> None:
        """Log habit-related events."""
        
        logger.info(f"Habit event: {event_type} for habit {habit.habit_id} (user: {habit.user_id})")
    
    def _get_fallback_habit_plan(self, desired_outcome: str) -> HabitFormationPlan:
        """Get fallback habit plan."""
        
        return HabitFormationPlan(
            habit_type=HabitType.DAILY_TRACKING,
            tiny_version="Check your finances for 1 minute",
            scaled_versions=["1 minute", "5 minutes", "10 minutes", "Full review"],
            trigger_options=[{'type': 'time', 'description': 'Morning routine'}],
            celebration_ideas=["Say 'Yes!' out loud", "Do a fist pump", "Smile"],
            potential_obstacles=["Forgetting", "Lack of time"],
            solutions={"Forgetting": "Set phone reminder", "Lack of time": "Start with 30 seconds"},
            success_metrics={'consistency': 0.8, 'streak_target': 7},
            timeline={'week_1': 'Establish routine', 'week_2-4': 'Build consistency'}
        )
    
    def _determine_frequency(self, habit_type: HabitType) -> str:
        """Determine optimal frequency for habit type."""
        
        daily_habits = [
            HabitType.DAILY_TRACKING,
            HabitType.EXPENSE_LOGGING,
            HabitType.SPENDING_PAUSE,
            HabitType.LEARNING_SESSION
        ]
        
        weekly_habits = [
            HabitType.WEEKLY_REVIEW,
            HabitType.GOAL_CHECK,
            HabitType.FINANCIAL_PLANNING
        ]
        
        if habit_type in daily_habits:
            return 'daily'
        elif habit_type in weekly_habits:
            return 'weekly'
        else:
            return 'monthly'
    
    def _initialize_behavior_map(self) -> Dict:
        """Initialize BJ Fogg behavior map."""
        
        return {
            'high_motivation_high_ability': ['complex_habits', 'multiple_habits'],
            'high_motivation_low_ability': ['simplify', 'tiny_habits'],
            'low_motivation_high_ability': ['make_attractive', 'add_rewards'],
            'low_motivation_low_ability': ['smallest_step', 'maximum_support']
        }
    
    def _initialize_tiny_habits(self) -> Dict:
        """Initialize library of tiny habits."""
        
        return {
            HabitType.DAILY_TRACKING: {
                'starter': 'Open finance app for 10 seconds',
                'easy': 'Check account balance',
                'moderate': 'Log one expense'
            },
            HabitType.SAVING_TRANSFER: {
                'starter': 'Move $1 to savings',
                'easy': 'Transfer $5 to savings',
                'moderate': 'Transfer 1% of income'
            },
            HabitType.EXPENSE_LOGGING: {
                'starter': 'Photo receipt of one purchase',
                'easy': 'Log purchases before bed',
                'moderate': 'Categorize all expenses'
            }
        }
    
    def _initialize_celebrations(self) -> Dict:
        """Initialize celebration library."""
        
        return {
            'universal': [
                'Say "I did it!" out loud',
                'Give yourself a high-five',
                'Do a victory dance',
                'Smile and nod',
                'Take a deep breath and feel proud'
            ],
            'saving_transfer': [
                'Watch savings balance grow',
                'Visualize future goal',
                'Add to vision board'
            ],
            'expense_logging': [
                'See spending insights update',
                'Check budget progress',
                'Share with accountability partner'
            ]
        }
    
    def _initialize_badge_system(self) -> Dict:
        """Initialize gamification badges."""
        
        return {
            'first_day': {'name': 'First Step', 'criteria': 'Complete first habit'},
            'week_warrior': {'name': 'Week Warrior', 'criteria': '7-day streak'},
            'monthly_master': {'name': 'Monthly Master', 'criteria': '30-day streak'},
            'consistency_champion': {'name': 'Consistency Champion', 'criteria': '90% completion rate'},
            'habit_stacker': {'name': 'Habit Stacker', 'criteria': 'Successfully stack 2 habits'},
            'level_upper': {'name': 'Level Upper', 'criteria': 'Progress through 3 difficulty levels'}
        }
    
    def _initialize_level_system(self) -> Dict:
        """Initialize progression levels."""
        
        return {
            1: {'name': 'Beginner', 'points_required': 0, 'perks': ['Basic tracking']},
            2: {'name': 'Apprentice', 'points_required': 100, 'perks': ['Habit stacking']},
            3: {'name': 'Practitioner', 'points_required': 500, 'perks': ['Advanced celebrations']},
            4: {'name': 'Expert', 'points_required': 1500, 'perks': ['Custom habits']},
            5: {'name': 'Master', 'points_required': 5000, 'perks': ['Mentor others']}
        }
    
    def _initialize_habit_stacks(self) -> Dict:
        """Initialize habit stacking templates."""
        
        return {
            'morning_routine': [
                'Check weather → Review daily budget',
                'Brush teeth → Log yesterday expenses',
                'Coffee → 1-minute financial check'
            ],
            'evening_routine': [
                'Dinner cleanup → Log day expenses',
                'Before bed → Tomorrow planning',
                'Set alarm → Schedule saving transfer'
            ],
            'work_routine': [
                'Arrive at work → Check financial goals',
                'Lunch break → Quick budget review',
                'End of workday → Log work expenses'
            ]
        }
    
    async def _generate_habit_summary(self, habits: List[FinancialHabit]) -> str:
        """Generate summary of habit progress."""
        
        if not habits:
            return "No active habits found. Start your first habit today!"
        
        active = sum(1 for h in habits if h.status == HabitStatus.ACTIVE)
        avg_completion = np.mean([h.metrics.completion_rate for h in habits]) if habits else 0
        total_streaks = sum(h.metrics.current_streak for h in habits)
        
        return f"You have {active} active habits with {avg_completion:.0%} average completion rate and {total_streaks} total streak days!"
    
    def _analyze_streaks(self, habits: List[FinancialHabit]) -> Dict:
        """Analyze streak patterns."""
        
        return {
            'current_streaks': {h.name: h.metrics.current_streak for h in habits},
            'longest_streaks': {h.name: h.metrics.longest_streak for h in habits},
            'total_streak_days': sum(h.metrics.current_streak for h in habits),
            'at_risk': [h.name for h in habits if 0 < h.metrics.current_streak < 3]
        }
    
    async def _analyze_completion_patterns(self, habits: List[FinancialHabit]) -> Dict:
        """Analyze completion patterns."""
        
        return {
            'best_performing': max(habits, key=lambda h: h.metrics.completion_rate).name if habits else None,
            'needs_attention': [h.name for h in habits if h.metrics.completion_rate < 0.5],
            'ready_to_scale': [h.name for h in habits if h.metrics.completion_rate > 0.9]
        }
    
    async def _identify_encountered_obstacles(self, habits: List[FinancialHabit]) -> List[str]:
        """Identify obstacles from habit notes."""
        
        obstacles = []
        for habit in habits:
            for note in habit.notes:
                if note.get('type') == 'obstacle':
                    obstacles.append(note.get('description', 'Unknown obstacle'))
        
        return list(set(obstacles))  # Unique obstacles
    
    async def _generate_habit_recommendations(self, habits: List[FinancialHabit]) -> List[str]:
        """Generate recommendations for habit improvement."""
        
        recommendations = []
        
        for habit in habits:
            if habit.metrics.completion_rate < 0.5:
                recommendations.append(f"Simplify {habit.name} or adjust trigger time")
            elif habit.metrics.current_streak == 0 and habit.metrics.total_completions > 0:
                recommendations.append(f"Restart {habit.name} with a tiny version")
            elif habit.metrics.completion_rate > 0.9 and habit.difficulty == HabitDifficulty.TINY:
                recommendations.append(f"Level up {habit.name} to next difficulty")
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _analyze_celebration_effectiveness(self, habits: List[FinancialHabit]) -> Dict:
        """Analyze which celebrations work best."""
        
        celebration_stats = {}
        for habit in habits:
            if habit.celebration_ritual:
                celebration_stats[habit.celebration_ritual] = {
                    'completion_rate': habit.metrics.completion_rate,
                    'streak': habit.metrics.current_streak
                }
        
        return celebration_stats
    
    async def _assess_behavior_change(self, habits: List[FinancialHabit]) -> Dict:
        """Assess overall behavior change progress."""
        
        if not habits:
            return {'status': 'No habits to assess'}
        
        avg_motivation = np.mean([h.motivation_level for h in habits])
        avg_ability = np.mean([h.ability_level for h in habits])
        avg_prompt = np.mean([h.prompt_effectiveness for h in habits])
        
        return {
            'motivation_trend': 'increasing' if avg_motivation > 0.6 else 'needs_boost',
            'ability_level': 'high' if avg_ability > 0.7 else 'developing',
            'prompt_dependency': 'low' if avg_prompt < 0.5 else 'high',
            'overall_progress': 'excellent' if avg_motivation > 0.7 and avg_ability > 0.7 else 'good'
        }
    
    async def _assess_stacking_compatibility(
        self,
        existing_habit: FinancialHabit,
        new_habit_type: HabitType
    ) -> float:
        """Assess compatibility for habit stacking."""
        
        # Simple compatibility scoring
        compatibility = 0.5
        
        # Same frequency increases compatibility
        new_frequency = self._determine_frequency(new_habit_type)
        if existing_habit.frequency == new_frequency:
            compatibility += 0.2
        
        # High completion rate increases compatibility
        if existing_habit.metrics.completion_rate > 0.8:
            compatibility += 0.2
        
        # Similar categories increase compatibility
        if 'tracking' in existing_habit.habit_type.value and 'tracking' in new_habit_type.value:
            compatibility += 0.1
        
        return min(1.0, compatibility)
    
    async def _suggest_stack_sequence(
        self,
        existing_habit: FinancialHabit,
        new_habit_type: HabitType
    ) -> str:
        """Suggest sequence for habit stacking."""
        
        return f"After {existing_habit.name}, immediately {new_habit_type.value.replace('_', ' ')}"
    
    async def _explain_stack_benefits(
        self,
        existing_habit: FinancialHabit,
        new_habit_type: HabitType
    ) -> List[str]:
        """Explain benefits of specific habit stack."""
        
        return [
            "Leverages existing habit momentum",
            "Reduces decision fatigue",
            "Creates powerful routine chain",
            "Increases overall completion rate"
        ]
    
    async def _create_resumption_plan(
        self,
        habit: FinancialHabit,
        reason: Optional[str]
    ) -> Dict:
        """Create plan for resuming paused habit."""
        
        return {
            'restart_date': (datetime.utcnow() + timedelta(days=3)).isoformat(),
            'restart_level': 'tiny',  # Always restart small
            'preparation_steps': [
                "Review your original motivation",
                "Set a specific restart date",
                "Prepare environment for success"
            ],
            'adjustments_suggested': [
                "Simplify the habit further",
                "Change trigger time if needed",
                "Find accountability partner"
            ]
        }
    
    async def _apply_habit_adjustments(
        self,
        habit: FinancialHabit,
        adjustments: Dict
    ) -> None:
        """Apply adjustments to habit."""
        
        if 'trigger_time' in adjustments:
            habit.trigger.specific_time = adjustments['trigger_time']
        
        if 'difficulty' in adjustments:
            habit.difficulty = HabitDifficulty(adjustments['difficulty'])
        
        if 'celebration' in adjustments:
            habit.celebration_ritual = adjustments['celebration']
        
        habit.updated_at = datetime.utcnow()
    
    async def _generate_resumption_encouragement(
        self,
        habit: FinancialHabit
    ) -> str:
        """Generate encouraging message for habit resumption."""
        
        messages = [
            f"Welcome back! Let's restart {habit.name} with a tiny win today.",
            f"Your previous {habit.metrics.total_completions} completions show you can do this!",
            "Starting again is a sign of commitment, not failure.",
            "Every expert was once a beginner who kept showing up."
        ]
        
        return " ".join(messages[:2])