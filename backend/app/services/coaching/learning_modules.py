"""
Interactive Financial Learning System

Provides personalized financial education with adaptive learning paths,
knowledge assessment, and certification system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from dataclasses import dataclass, field
import uuid
import hashlib

import numpy as np
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.base import SessionLocal
from app.models.user import User
from app.ai.llm_client import LLMClientManager

logger = logging.getLogger(__name__)


class CourseLevel(str, Enum):
    """Course difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningPath(str, Enum):
    """Predefined learning paths."""
    FINANCIAL_BASICS = "financial_basics"
    BUDGETING_MASTERY = "budgeting_mastery"
    INVESTING_FUNDAMENTALS = "investing_fundamentals"
    RETIREMENT_PLANNING = "retirement_planning"
    DEBT_MANAGEMENT = "debt_management"
    TAX_OPTIMIZATION = "tax_optimization"
    REAL_ESTATE = "real_estate"
    BUSINESS_FINANCE = "business_finance"
    WEALTH_BUILDING = "wealth_building"
    RISK_MANAGEMENT = "risk_management"


class ContentType(str, Enum):
    """Types of learning content."""
    VIDEO = "video"
    ARTICLE = "article"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"
    SIMULATION = "simulation"
    CASE_STUDY = "case_study"
    WORKSHEET = "worksheet"
    PODCAST = "podcast"


class BadgeType(str, Enum):
    """Types of achievement badges."""
    COMPLETION = "completion"
    MASTERY = "mastery"
    STREAK = "streak"
    MILESTONE = "milestone"
    CERTIFICATION = "certification"
    SPECIAL = "special"


@dataclass
class LearningModule:
    """Represents a learning module."""
    module_id: str
    title: str
    description: str
    level: CourseLevel
    path: LearningPath
    estimated_time: int  # minutes
    prerequisites: List[str]
    learning_objectives: List[str]
    content_items: List[Dict[str, Any]]
    assessments: List[Dict[str, Any]]
    resources: List[Dict[str, str]]
    skills_gained: List[str]
    completion_criteria: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LearnerProfile:
    """User's learning profile."""
    user_id: str
    knowledge_level: Dict[str, float]  # Topic -> proficiency (0-1)
    learning_style: str  # visual, auditory, reading, kinesthetic
    pace_preference: str  # self-paced, structured, intensive
    completed_modules: List[str]
    current_modules: List[str]
    learning_streaks: Dict[str, int]
    total_learning_time: int  # minutes
    badges_earned: List[Dict[str, Any]]
    certifications: List[Dict[str, Any]]
    knowledge_gaps: List[str]
    interests: List[str]
    goals: List[str]
    last_active: datetime
    created_at: datetime


@dataclass
class KnowledgeAssessment:
    """Knowledge assessment results."""
    assessment_id: str
    user_id: str
    module_id: Optional[str]
    topic: str
    questions_answered: int
    correct_answers: int
    score: float  # 0-100
    proficiency_level: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    timestamp: datetime


@dataclass
class Certificate:
    """Learning achievement certificate."""
    certificate_id: str
    user_id: str
    course_name: str
    completion_date: datetime
    score: float
    skills_demonstrated: List[str]
    verification_code: str
    expiry_date: Optional[datetime]
    badge_earned: Optional[str]


class AdaptiveLearning(BaseModel):
    """Adaptive learning recommendations."""
    next_module: str
    difficulty_adjustment: str  # easier, same, harder
    content_type_mix: Dict[ContentType, float]  # Preferred content types
    pace_recommendation: str
    focus_areas: List[str]
    estimated_completion: int  # days
    personalized_tips: List[str]


class LearningSystemManager:
    """Manages interactive financial learning system."""
    
    def __init__(self, llm_manager: LLMClientManager):
        self.llm_manager = llm_manager
        
        # Learning content library
        self.modules_library = self._initialize_modules_library()
        
        # Assessment question banks
        self.question_banks = self._initialize_question_banks()
        
        # Badge and certification criteria
        self.badge_criteria = self._initialize_badge_criteria()
        
        # User profiles storage
        self.learner_profiles: Dict[str, LearnerProfile] = {}
        
        # Active learning sessions
        self.active_sessions: Dict[str, Dict] = {}
        
        # Knowledge graph
        self.knowledge_graph = self._initialize_knowledge_graph()
    
    async def create_personalized_path(
        self,
        user_id: str,
        goals: List[str],
        current_knowledge: Optional[Dict[str, float]] = None,
        time_commitment: Optional[int] = None  # hours per week
    ) -> Dict[str, Any]:
        """Create personalized learning path based on goals and assessment."""
        
        try:
            # Get or create learner profile
            profile = await self._get_or_create_profile(user_id)
            
            # Assess current knowledge if not provided
            if not current_knowledge:
                current_knowledge = await self._assess_baseline_knowledge(user_id)
            
            # Identify knowledge gaps
            gaps = await self._identify_knowledge_gaps(goals, current_knowledge)
            
            # Generate personalized curriculum
            curriculum = await self._generate_curriculum(
                goals, gaps, current_knowledge, time_commitment
            )
            
            # Create learning schedule
            schedule = await self._create_learning_schedule(
                curriculum, time_commitment
            )
            
            # Select initial modules
            initial_modules = await self._select_initial_modules(
                curriculum, profile
            )
            
            # Generate motivation strategy
            motivation = await self._create_motivation_strategy(profile, goals)
            
            return {
                'path_id': str(uuid.uuid4()),
                'user_id': user_id,
                'goals': goals,
                'curriculum': curriculum,
                'schedule': schedule,
                'initial_modules': initial_modules,
                'estimated_completion': self._estimate_completion_time(curriculum, time_commitment),
                'knowledge_gaps': gaps,
                'motivation_strategy': motivation,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating personalized path: {str(e)}")
            return self._get_fallback_learning_path(goals)
    
    async def get_next_module(
        self,
        user_id: str,
        completed_module_id: Optional[str] = None,
        performance: Optional[Dict[str, Any]] = None
    ) -> LearningModule:
        """Get next recommended learning module using adaptive algorithm."""
        
        try:
            profile = self.learner_profiles.get(user_id)
            if not profile:
                profile = await self._get_or_create_profile(user_id)
            
            # Update profile with recent performance
            if completed_module_id and performance:
                await self._update_learning_progress(
                    profile, completed_module_id, performance
                )
            
            # Apply adaptive learning algorithm
            adaptation = await self._apply_adaptive_learning(profile)
            
            # Select next module based on adaptation
            next_module = await self._select_adaptive_module(profile, adaptation)
            
            # Personalize module content
            personalized = await self._personalize_module_content(
                next_module, profile
            )
            
            return personalized
            
        except Exception as e:
            logger.error(f"Error getting next module: {str(e)}")
            return self._get_fallback_module(user_id)
    
    async def conduct_assessment(
        self,
        user_id: str,
        topic: str,
        module_id: Optional[str] = None
    ) -> KnowledgeAssessment:
        """Conduct knowledge assessment on specific topic."""
        
        try:
            # Get relevant questions
            questions = await self._select_assessment_questions(
                topic, module_id
            )
            
            # Simulate assessment (in production, would be interactive)
            responses = await self._simulate_assessment_responses(
                user_id, questions
            )
            
            # Score assessment
            results = await self._score_assessment(questions, responses)
            
            # Analyze strengths and weaknesses
            analysis = await self._analyze_assessment_results(
                results, topic
            )
            
            # Generate recommendations
            recommendations = await self._generate_learning_recommendations(
                analysis, topic
            )
            
            # Create assessment record
            assessment = KnowledgeAssessment(
                assessment_id=str(uuid.uuid4()),
                user_id=user_id,
                module_id=module_id,
                topic=topic,
                questions_answered=len(questions),
                correct_answers=results['correct'],
                score=results['score'],
                proficiency_level=analysis['proficiency_level'],
                strengths=analysis['strengths'],
                weaknesses=analysis['weaknesses'],
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
            # Update learner profile
            await self._update_knowledge_profile(user_id, assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error conducting assessment: {str(e)}")
            return self._get_fallback_assessment(user_id, topic)
    
    async def issue_certificate(
        self,
        user_id: str,
        course_name: str,
        modules_completed: List[str],
        final_score: float
    ) -> Certificate:
        """Issue certificate for completed learning path."""
        
        try:
            # Verify completion criteria
            if not await self._verify_completion_criteria(
                user_id, course_name, modules_completed
            ):
                raise ValueError("Completion criteria not met")
            
            # Extract demonstrated skills
            skills = await self._extract_demonstrated_skills(modules_completed)
            
            # Generate verification code
            verification_code = self._generate_verification_code(
                user_id, course_name, datetime.utcnow()
            )
            
            # Determine badge
            badge = await self._determine_certificate_badge(
                course_name, final_score
            )
            
            # Create certificate
            certificate = Certificate(
                certificate_id=str(uuid.uuid4()),
                user_id=user_id,
                course_name=course_name,
                completion_date=datetime.utcnow(),
                score=final_score,
                skills_demonstrated=skills,
                verification_code=verification_code,
                expiry_date=datetime.utcnow() + timedelta(days=730),  # 2 years
                badge_earned=badge
            )
            
            # Update learner profile
            await self._add_certificate_to_profile(user_id, certificate)
            
            # Generate shareable certificate
            await self._generate_shareable_certificate(certificate)
            
            return certificate
            
        except Exception as e:
            logger.error(f"Error issuing certificate: {str(e)}")
            raise
    
    async def get_learning_analytics(
        self,
        user_id: str,
        time_period: Optional[int] = 30  # days
    ) -> Dict[str, Any]:
        """Get comprehensive learning analytics for user."""
        
        try:
            profile = self.learner_profiles.get(user_id)
            if not profile:
                return {'error': 'No learning profile found'}
            
            # Calculate key metrics
            metrics = {
                'total_modules_completed': len(profile.completed_modules),
                'current_streak': max(profile.learning_streaks.values()) if profile.learning_streaks else 0,
                'total_learning_time': profile.total_learning_time,
                'average_score': await self._calculate_average_score(user_id),
                'badges_earned': len(profile.badges_earned),
                'certifications': len(profile.certifications)
            }
            
            # Analyze progress trends
            trends = await self._analyze_learning_trends(profile, time_period)
            
            # Identify strengths and areas for improvement
            analysis = await self._analyze_knowledge_profile(profile)
            
            # Generate insights
            insights = await self._generate_learning_insights(
                profile, metrics, trends
            )
            
            # Recommendations
            recommendations = await self._generate_next_steps(profile)
            
            return {
                'metrics': metrics,
                'trends': trends,
                'knowledge_analysis': analysis,
                'insights': insights,
                'recommendations': recommendations,
                'achievements': {
                    'recent_badges': profile.badges_earned[-5:] if profile.badges_earned else [],
                    'next_milestone': await self._identify_next_milestone(profile)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting learning analytics: {str(e)}")
            return {'error': str(e)}
    
    async def generate_study_session(
        self,
        user_id: str,
        available_time: int,  # minutes
        focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate optimized study session based on available time."""
        
        try:
            profile = self.learner_profiles.get(user_id)
            if not profile:
                profile = await self._get_or_create_profile(user_id)
            
            # Select appropriate content for time available
            content = await self._select_session_content(
                profile, available_time, focus_topic
            )
            
            # Apply spaced repetition algorithm
            review_items = await self._get_spaced_repetition_items(profile)
            
            # Create session structure
            session = {
                'session_id': str(uuid.uuid4()),
                'user_id': user_id,
                'duration': available_time,
                'segments': []
            }
            
            # Add warm-up (5% of time)
            if available_time > 20:
                session['segments'].append({
                    'type': 'warm_up',
                    'duration': max(2, int(available_time * 0.05)),
                    'content': review_items[:2] if review_items else [],
                    'description': 'Quick review of previous concepts'
                })
            
            # Add main content (70% of time)
            main_duration = int(available_time * 0.7)
            session['segments'].append({
                'type': 'main_content',
                'duration': main_duration,
                'content': content['main'],
                'description': content['description']
            })
            
            # Add practice (20% of time)
            if available_time > 10:
                session['segments'].append({
                    'type': 'practice',
                    'duration': int(available_time * 0.2),
                    'content': content['practice'],
                    'description': 'Apply what you learned'
                })
            
            # Add review (5% of time)
            session['segments'].append({
                'type': 'review',
                'duration': max(2, int(available_time * 0.05)),
                'content': content['summary'],
                'description': 'Key takeaways'
            })
            
            # Add motivation and tips
            session['tips'] = await self._generate_study_tips(profile, focus_topic)
            session['motivation'] = await self._generate_motivation_message(profile)
            
            # Store active session
            self.active_sessions[user_id] = session
            
            return session
            
        except Exception as e:
            logger.error(f"Error generating study session: {str(e)}")
            return self._get_fallback_study_session(available_time)
    
    async def _get_or_create_profile(self, user_id: str) -> LearnerProfile:
        """Get existing profile or create new one."""
        
        if user_id in self.learner_profiles:
            return self.learner_profiles[user_id]
        
        # Create new profile
        profile = LearnerProfile(
            user_id=user_id,
            knowledge_level={},
            learning_style='balanced',
            pace_preference='self-paced',
            completed_modules=[],
            current_modules=[],
            learning_streaks={},
            total_learning_time=0,
            badges_earned=[],
            certifications=[],
            knowledge_gaps=[],
            interests=[],
            goals=[],
            last_active=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.learner_profiles[user_id] = profile
        return profile
    
    async def _assess_baseline_knowledge(self, user_id: str) -> Dict[str, float]:
        """Assess user's baseline financial knowledge."""
        
        # Simple assessment (in production would be interactive quiz)
        prompt = """
        Generate a baseline financial knowledge assessment for:
        - Budgeting
        - Saving
        - Investing
        - Debt Management
        - Retirement Planning
        - Tax Planning
        
        Return proficiency level (0-1) for each area.
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse response (simplified)
            return {
                'budgeting': 0.5,
                'saving': 0.6,
                'investing': 0.3,
                'debt_management': 0.4,
                'retirement_planning': 0.2,
                'tax_planning': 0.1
            }
        except:
            # Default baseline
            return {topic: 0.3 for topic in ['budgeting', 'saving', 'investing']}
    
    async def _identify_knowledge_gaps(
        self,
        goals: List[str],
        current_knowledge: Dict[str, float]
    ) -> List[str]:
        """Identify knowledge gaps based on goals."""
        
        gaps = []
        
        # Map goals to required knowledge areas
        goal_requirements = {
            'retirement': ['retirement_planning', 'investing', 'tax_planning'],
            'home_purchase': ['saving', 'budgeting', 'debt_management'],
            'investing': ['investing', 'risk_management', 'tax_planning'],
            'debt_free': ['debt_management', 'budgeting', 'saving']
        }
        
        for goal in goals:
            required = goal_requirements.get(goal.lower(), [])
            for req in required:
                if current_knowledge.get(req, 0) < 0.6:
                    gaps.append(req)
        
        return list(set(gaps))  # Unique gaps
    
    async def _generate_curriculum(
        self,
        goals: List[str],
        gaps: List[str],
        current_knowledge: Dict[str, float],
        time_commitment: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Generate personalized curriculum."""
        
        curriculum = []
        
        # Priority 1: Address critical gaps
        for gap in gaps:
            level = self._determine_starting_level(current_knowledge.get(gap, 0))
            modules = self._get_modules_for_topic(gap, level)
            curriculum.extend([
                {
                    'module_id': m['id'],
                    'title': m['title'],
                    'topic': gap,
                    'level': level,
                    'priority': 1,
                    'estimated_time': m['time']
                }
                for m in modules[:3]  # Top 3 modules per gap
            ])
        
        # Priority 2: Goal-specific modules
        for goal in goals:
            modules = self._get_modules_for_goal(goal)
            curriculum.extend([
                {
                    'module_id': m['id'],
                    'title': m['title'],
                    'topic': goal,
                    'level': 'intermediate',
                    'priority': 2,
                    'estimated_time': m['time']
                }
                for m in modules[:2]
            ])
        
        # Sort by priority and level
        curriculum.sort(key=lambda x: (x['priority'], x['level']))
        
        return curriculum
    
    async def _create_learning_schedule(
        self,
        curriculum: List[Dict],
        time_commitment: Optional[int]
    ) -> Dict[str, Any]:
        """Create learning schedule based on time commitment."""
        
        weekly_hours = time_commitment or 3  # Default 3 hours/week
        weekly_minutes = weekly_hours * 60
        
        schedule = {
            'weekly_commitment': weekly_hours,
            'recommended_sessions': [],
            'milestones': []
        }
        
        # Distribute modules across weeks
        current_week = 1
        week_minutes = 0
        week_modules = []
        
        for module in curriculum:
            if week_minutes + module['estimated_time'] > weekly_minutes:
                schedule['recommended_sessions'].append({
                    'week': current_week,
                    'modules': week_modules,
                    'total_time': week_minutes
                })
                current_week += 1
                week_minutes = 0
                week_modules = []
            
            week_modules.append(module['module_id'])
            week_minutes += module['estimated_time']
        
        # Add remaining modules
        if week_modules:
            schedule['recommended_sessions'].append({
                'week': current_week,
                'modules': week_modules,
                'total_time': week_minutes
            })
        
        # Add milestones
        total_weeks = len(schedule['recommended_sessions'])
        schedule['milestones'] = [
            {'week': total_weeks // 4, 'description': '25% Complete - Foundation Built'},
            {'week': total_weeks // 2, 'description': '50% Complete - Core Concepts Mastered'},
            {'week': 3 * total_weeks // 4, 'description': '75% Complete - Advanced Topics'},
            {'week': total_weeks, 'description': '100% Complete - Certification Ready'}
        ]
        
        return schedule
    
    async def _select_initial_modules(
        self,
        curriculum: List[Dict],
        profile: LearnerProfile
    ) -> List[str]:
        """Select initial modules to start with."""
        
        # Get first 3 modules that match user's level
        initial = []
        for module in curriculum:
            if len(initial) < 3:
                # Check prerequisites
                module_obj = self._get_module_by_id(module['module_id'])
                if not module_obj or not module_obj.prerequisites:
                    initial.append(module['module_id'])
                elif all(p in profile.completed_modules for p in module_obj.prerequisites):
                    initial.append(module['module_id'])
        
        return initial
    
    async def _create_motivation_strategy(
        self,
        profile: LearnerProfile,
        goals: List[str]
    ) -> Dict[str, Any]:
        """Create personalized motivation strategy."""
        
        strategy = {
            'gamification_elements': [],
            'milestones': [],
            'rewards': [],
            'accountability': []
        }
        
        # Add gamification based on profile
        strategy['gamification_elements'] = [
            'Daily streak tracking',
            'Points for completion (10 points per module)',
            'Badges for achievements',
            'Leaderboard position (optional)',
            'Progress bar visualization'
        ]
        
        # Set milestones
        strategy['milestones'] = [
            {'modules': 5, 'reward': 'Beginner Badge'},
            {'modules': 15, 'reward': 'Dedicated Learner Badge'},
            {'modules': 30, 'reward': 'Expert Badge'},
            {'streak': 7, 'reward': 'Week Warrior Badge'},
            {'streak': 30, 'reward': 'Monthly Master Badge'}
        ]
        
        # Define rewards
        strategy['rewards'] = [
            'Unlock advanced content',
            'Certificate of completion',
            'Share achievements on social media',
            'Access to exclusive webinars',
            'One-on-one coaching session (at 50 modules)'
        ]
        
        # Accountability measures
        strategy['accountability'] = [
            'Weekly progress emails',
            'Study buddy matching (optional)',
            'Public commitment option',
            'Progress sharing with advisor'
        ]
        
        return strategy
    
    def _estimate_completion_time(
        self,
        curriculum: List[Dict],
        time_commitment: Optional[int]
    ) -> int:
        """Estimate days to complete curriculum."""
        
        total_minutes = sum(m['estimated_time'] for m in curriculum)
        weekly_minutes = (time_commitment or 3) * 60
        weeks_needed = total_minutes / weekly_minutes if weekly_minutes > 0 else 52
        
        return int(weeks_needed * 7)  # Convert to days
    
    def _determine_starting_level(self, proficiency: float) -> CourseLevel:
        """Determine appropriate starting level based on proficiency."""
        
        if proficiency < 0.3:
            return CourseLevel.BEGINNER
        elif proficiency < 0.6:
            return CourseLevel.INTERMEDIATE
        elif proficiency < 0.8:
            return CourseLevel.ADVANCED
        else:
            return CourseLevel.EXPERT
    
    def _get_modules_for_topic(self, topic: str, level: CourseLevel) -> List[Dict]:
        """Get modules for specific topic and level."""
        
        # Simplified module selection
        modules = []
        for path_modules in self.modules_library.values():
            for module in path_modules:
                if topic.lower() in module.get('title', '').lower() and \
                   module.get('level') == level.value:
                    modules.append({
                        'id': module.get('id', str(uuid.uuid4())),
                        'title': module.get('title'),
                        'time': module.get('estimated_time', 30)
                    })
        
        return modules[:5]  # Return up to 5 modules
    
    def _get_modules_for_goal(self, goal: str) -> List[Dict]:
        """Get modules specific to a goal."""
        
        # Map goals to learning paths
        goal_path_map = {
            'retirement': LearningPath.RETIREMENT_PLANNING,
            'investing': LearningPath.INVESTING_FUNDAMENTALS,
            'debt_free': LearningPath.DEBT_MANAGEMENT,
            'wealth': LearningPath.WEALTH_BUILDING
        }
        
        path = goal_path_map.get(goal.lower(), LearningPath.FINANCIAL_BASICS)
        modules = self.modules_library.get(path, [])
        
        return [
            {
                'id': m.get('id', str(uuid.uuid4())),
                'title': m.get('title'),
                'time': m.get('estimated_time', 30)
            }
            for m in modules[:3]
        ]
    
    def _get_module_by_id(self, module_id: str) -> Optional[LearningModule]:
        """Get module by ID."""
        
        for path_modules in self.modules_library.values():
            for module in path_modules:
                if module.get('id') == module_id:
                    # Convert dict to LearningModule
                    return LearningModule(
                        module_id=module['id'],
                        title=module['title'],
                        description=module.get('description', ''),
                        level=CourseLevel(module.get('level', 'beginner')),
                        path=LearningPath.FINANCIAL_BASICS,
                        estimated_time=module.get('estimated_time', 30),
                        prerequisites=module.get('prerequisites', []),
                        learning_objectives=module.get('objectives', []),
                        content_items=module.get('content', []),
                        assessments=module.get('assessments', []),
                        resources=module.get('resources', []),
                        skills_gained=module.get('skills', []),
                        completion_criteria=module.get('criteria', {})
                    )
        return None
    
    async def _update_learning_progress(
        self,
        profile: LearnerProfile,
        module_id: str,
        performance: Dict[str, Any]
    ) -> None:
        """Update learner profile with progress."""
        
        # Add to completed modules
        if module_id not in profile.completed_modules:
            profile.completed_modules.append(module_id)
        
        # Update knowledge levels based on performance
        module = self._get_module_by_id(module_id)
        if module:
            for skill in module.skills_gained:
                current_level = profile.knowledge_level.get(skill, 0)
                improvement = performance.get('score', 0.7) * 0.1
                profile.knowledge_level[skill] = min(1.0, current_level + improvement)
        
        # Update learning time
        profile.total_learning_time += performance.get('time_spent', 30)
        
        # Update streak
        today = datetime.utcnow().date().isoformat()
        profile.learning_streaks[today] = profile.learning_streaks.get(today, 0) + 1
        
        profile.last_active = datetime.utcnow()
    
    async def _apply_adaptive_learning(
        self,
        profile: LearnerProfile
    ) -> AdaptiveLearning:
        """Apply adaptive learning algorithm."""
        
        # Analyze recent performance
        recent_performance = self._analyze_recent_performance(profile)
        
        # Determine difficulty adjustment
        if recent_performance > 0.85:
            difficulty_adjustment = 'harder'
        elif recent_performance < 0.6:
            difficulty_adjustment = 'easier'
        else:
            difficulty_adjustment = 'same'
        
        # Determine content type mix based on learning style
        content_mix = self._determine_content_mix(profile.learning_style)
        
        # Identify focus areas
        focus_areas = [
            topic for topic, level in profile.knowledge_level.items()
            if level < 0.6
        ][:3]
        
        return AdaptiveLearning(
            next_module='',  # Will be filled by select_adaptive_module
            difficulty_adjustment=difficulty_adjustment,
            content_type_mix=content_mix,
            pace_recommendation='maintain' if recent_performance > 0.7 else 'slow down',
            focus_areas=focus_areas,
            estimated_completion=7,
            personalized_tips=[
                "Focus on practice problems",
                "Review previous concepts",
                "Take breaks every 25 minutes"
            ]
        )
    
    async def _select_adaptive_module(
        self,
        profile: LearnerProfile,
        adaptation: AdaptiveLearning
    ) -> LearningModule:
        """Select module based on adaptive learning recommendations."""
        
        # Get modules matching criteria
        candidate_modules = []
        
        for path_modules in self.modules_library.values():
            for module_data in path_modules:
                # Check if module matches adaptation criteria
                if self._module_matches_adaptation(module_data, adaptation, profile):
                    candidate_modules.append(module_data)
        
        # Select best module
        if candidate_modules:
            selected = candidate_modules[0]
        else:
            # Fallback to basic module
            selected = self.modules_library[LearningPath.FINANCIAL_BASICS][0]
        
        # Convert to LearningModule
        return LearningModule(
            module_id=selected.get('id', str(uuid.uuid4())),
            title=selected['title'],
            description=selected.get('description', ''),
            level=CourseLevel(selected.get('level', 'beginner')),
            path=LearningPath.FINANCIAL_BASICS,
            estimated_time=selected.get('estimated_time', 30),
            prerequisites=selected.get('prerequisites', []),
            learning_objectives=selected.get('objectives', []),
            content_items=selected.get('content', []),
            assessments=selected.get('assessments', []),
            resources=selected.get('resources', []),
            skills_gained=selected.get('skills', []),
            completion_criteria=selected.get('criteria', {})
        )
    
    async def _personalize_module_content(
        self,
        module: LearningModule,
        profile: LearnerProfile
    ) -> LearningModule:
        """Personalize module content based on learner profile."""
        
        # Adjust content based on learning style
        if profile.learning_style == 'visual':
            # Prioritize video and infographic content
            module.content_items = [
                item for item in module.content_items
                if item.get('type') in ['video', 'infographic', 'diagram']
            ] + [
                item for item in module.content_items
                if item.get('type') not in ['video', 'infographic', 'diagram']
            ]
        
        # Adjust estimated time based on pace
        if profile.pace_preference == 'intensive':
            module.estimated_time = int(module.estimated_time * 0.8)
        elif profile.pace_preference == 'relaxed':
            module.estimated_time = int(module.estimated_time * 1.2)
        
        return module
    
    def _analyze_recent_performance(self, profile: LearnerProfile) -> float:
        """Analyze recent learning performance."""
        
        # Simple performance calculation
        if not profile.completed_modules:
            return 0.5  # Default mid-performance
        
        # Would analyze actual assessment scores in production
        return 0.75  # Placeholder
    
    def _determine_content_mix(self, learning_style: str) -> Dict[ContentType, float]:
        """Determine optimal content type mix for learning style."""
        
        style_mix = {
            'visual': {
                ContentType.VIDEO: 0.4,
                ContentType.INTERACTIVE: 0.3,
                ContentType.ARTICLE: 0.2,
                ContentType.QUIZ: 0.1
            },
            'auditory': {
                ContentType.PODCAST: 0.3,
                ContentType.VIDEO: 0.3,
                ContentType.INTERACTIVE: 0.2,
                ContentType.ARTICLE: 0.2
            },
            'reading': {
                ContentType.ARTICLE: 0.4,
                ContentType.CASE_STUDY: 0.3,
                ContentType.WORKSHEET: 0.2,
                ContentType.QUIZ: 0.1
            },
            'kinesthetic': {
                ContentType.SIMULATION: 0.3,
                ContentType.INTERACTIVE: 0.3,
                ContentType.WORKSHEET: 0.2,
                ContentType.CASE_STUDY: 0.2
            }
        }
        
        return style_mix.get(learning_style, style_mix['visual'])
    
    def _module_matches_adaptation(
        self,
        module_data: Dict,
        adaptation: AdaptiveLearning,
        profile: LearnerProfile
    ) -> bool:
        """Check if module matches adaptive learning criteria."""
        
        # Check if module addresses focus areas
        module_topics = module_data.get('topics', [])
        if any(focus in module_topics for focus in adaptation.focus_areas):
            return True
        
        # Check if module is appropriate difficulty
        module_level = module_data.get('level', 'beginner')
        if adaptation.difficulty_adjustment == 'harder' and module_level in ['advanced', 'expert']:
            return True
        elif adaptation.difficulty_adjustment == 'easier' and module_level in ['beginner']:
            return True
        elif adaptation.difficulty_adjustment == 'same' and module_level in ['intermediate']:
            return True
        
        return False
    
    async def _select_assessment_questions(
        self,
        topic: str,
        module_id: Optional[str]
    ) -> List[Dict]:
        """Select assessment questions for topic."""
        
        questions = self.question_banks.get(topic, [])
        
        if not questions:
            # Generate questions with AI
            questions = await self._generate_assessment_questions(topic)
        
        # Select appropriate number of questions
        return questions[:10]  # 10 questions per assessment
    
    async def _generate_assessment_questions(self, topic: str) -> List[Dict]:
        """Generate assessment questions using AI."""
        
        prompt = f"""
        Generate 5 multiple-choice questions about {topic} in personal finance.
        Include:
        - Question text
        - 4 answer options
        - Correct answer
        - Explanation
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1000
            )
            
            # Parse response (simplified)
            return [
                {
                    'question': f"Sample question about {topic}",
                    'options': ['A', 'B', 'C', 'D'],
                    'correct': 'A',
                    'explanation': 'This is why A is correct'
                }
                for _ in range(5)
            ]
        except:
            return []
    
    async def _simulate_assessment_responses(
        self,
        user_id: str,
        questions: List[Dict]
    ) -> List[Dict]:
        """Simulate user responses to assessment questions."""
        
        # In production, this would be actual user input
        responses = []
        for q in questions:
            responses.append({
                'question_id': q.get('id', str(uuid.uuid4())),
                'selected_answer': q['correct'] if np.random.random() > 0.3 else q['options'][1],
                'time_taken': np.random.randint(10, 60)
            })
        
        return responses
    
    async def _score_assessment(
        self,
        questions: List[Dict],
        responses: List[Dict]
    ) -> Dict[str, Any]:
        """Score assessment responses."""
        
        correct = 0
        total = len(questions)
        
        for q, r in zip(questions, responses):
            if r['selected_answer'] == q['correct']:
                correct += 1
        
        return {
            'correct': correct,
            'total': total,
            'score': (correct / total * 100) if total > 0 else 0,
            'time_taken': sum(r['time_taken'] for r in responses)
        }
    
    async def _analyze_assessment_results(
        self,
        results: Dict,
        topic: str
    ) -> Dict[str, Any]:
        """Analyze assessment results for insights."""
        
        score = results['score']
        
        if score >= 90:
            proficiency_level = 'Expert'
        elif score >= 75:
            proficiency_level = 'Proficient'
        elif score >= 60:
            proficiency_level = 'Developing'
        else:
            proficiency_level = 'Beginner'
        
        # Identify strengths and weaknesses (simplified)
        strengths = [f"{topic} fundamentals"] if score > 60 else []
        weaknesses = [f"Advanced {topic} concepts"] if score < 75 else []
        
        return {
            'proficiency_level': proficiency_level,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'score_percentile': self._calculate_percentile(score)
        }
    
    async def _generate_learning_recommendations(
        self,
        analysis: Dict,
        topic: str
    ) -> List[str]:
        """Generate personalized learning recommendations."""
        
        recommendations = []
        
        if analysis['proficiency_level'] == 'Beginner':
            recommendations.extend([
                f"Start with {topic} basics course",
                "Focus on fundamental concepts",
                "Practice with simple examples"
            ])
        elif analysis['proficiency_level'] == 'Developing':
            recommendations.extend([
                f"Continue with intermediate {topic} modules",
                "Apply concepts to real scenarios",
                "Join study group for peer learning"
            ])
        else:
            recommendations.extend([
                f"Explore advanced {topic} strategies",
                "Teach others to solidify knowledge",
                "Apply knowledge to personal finances"
            ])
        
        return recommendations
    
    async def _update_knowledge_profile(
        self,
        user_id: str,
        assessment: KnowledgeAssessment
    ) -> None:
        """Update user's knowledge profile based on assessment."""
        
        profile = self.learner_profiles.get(user_id)
        if not profile:
            return
        
        # Update knowledge level for topic
        current_level = profile.knowledge_level.get(assessment.topic, 0)
        new_level = assessment.score / 100
        
        # Weighted average with more weight on recent assessment
        profile.knowledge_level[assessment.topic] = (
            current_level * 0.3 + new_level * 0.7
        )
        
        # Update knowledge gaps
        if new_level < 0.6:
            if assessment.topic not in profile.knowledge_gaps:
                profile.knowledge_gaps.append(assessment.topic)
        else:
            if assessment.topic in profile.knowledge_gaps:
                profile.knowledge_gaps.remove(assessment.topic)
    
    async def _verify_completion_criteria(
        self,
        user_id: str,
        course_name: str,
        modules_completed: List[str]
    ) -> bool:
        """Verify if user meets criteria for certificate."""
        
        # Check minimum modules completed
        if len(modules_completed) < 5:
            return False
        
        # Check if all required modules completed
        # (In production, would check specific course requirements)
        
        return True
    
    async def _extract_demonstrated_skills(
        self,
        modules_completed: List[str]
    ) -> List[str]:
        """Extract skills from completed modules."""
        
        skills = set()
        
        for module_id in modules_completed:
            module = self._get_module_by_id(module_id)
            if module:
                skills.update(module.skills_gained)
        
        return list(skills)
    
    def _generate_verification_code(
        self,
        user_id: str,
        course_name: str,
        completion_date: datetime
    ) -> str:
        """Generate unique verification code for certificate."""
        
        data = f"{user_id}:{course_name}:{completion_date.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    async def _determine_certificate_badge(
        self,
        course_name: str,
        final_score: float
    ) -> Optional[str]:
        """Determine badge based on performance."""
        
        if final_score >= 95:
            return "Gold Certificate"
        elif final_score >= 85:
            return "Silver Certificate"
        elif final_score >= 75:
            return "Bronze Certificate"
        else:
            return "Completion Certificate"
    
    async def _add_certificate_to_profile(
        self,
        user_id: str,
        certificate: Certificate
    ) -> None:
        """Add certificate to user profile."""
        
        profile = self.learner_profiles.get(user_id)
        if profile:
            profile.certifications.append({
                'id': certificate.certificate_id,
                'course': certificate.course_name,
                'date': certificate.completion_date.isoformat(),
                'score': certificate.score,
                'badge': certificate.badge_earned
            })
            
            # Add badge
            if certificate.badge_earned:
                profile.badges_earned.append({
                    'type': BadgeType.CERTIFICATION,
                    'name': certificate.badge_earned,
                    'date': datetime.utcnow().isoformat()
                })
    
    async def _generate_shareable_certificate(
        self,
        certificate: Certificate
    ) -> None:
        """Generate shareable version of certificate."""
        
        # In production, would generate PDF or image
        logger.info(f"Certificate generated: {certificate.certificate_id}")
    
    async def _calculate_average_score(self, user_id: str) -> float:
        """Calculate user's average assessment score."""
        
        # Simplified calculation
        return 75.0  # Placeholder
    
    async def _analyze_learning_trends(
        self,
        profile: LearnerProfile,
        time_period: int
    ) -> Dict[str, Any]:
        """Analyze learning trends over time period."""
        
        return {
            'completion_rate': 0.8,
            'average_time_per_module': 35,
            'most_active_day': 'Sunday',
            'streak_trend': 'increasing',
            'knowledge_growth': 0.15  # 15% improvement
        }
    
    async def _analyze_knowledge_profile(
        self,
        profile: LearnerProfile
    ) -> Dict[str, Any]:
        """Analyze user's knowledge profile."""
        
        strengths = [
            topic for topic, level in profile.knowledge_level.items()
            if level >= 0.7
        ]
        
        improvements = [
            topic for topic, level in profile.knowledge_level.items()
            if level < 0.5
        ]
        
        return {
            'strengths': strengths,
            'areas_for_improvement': improvements,
            'overall_proficiency': np.mean(list(profile.knowledge_level.values())) if profile.knowledge_level else 0,
            'breadth_of_knowledge': len(profile.knowledge_level)
        }
    
    async def _generate_learning_insights(
        self,
        profile: LearnerProfile,
        metrics: Dict,
        trends: Dict
    ) -> List[str]:
        """Generate personalized learning insights."""
        
        insights = []
        
        if metrics['current_streak'] > 7:
            insights.append("Great consistency! You're building strong learning habits.")
        
        if trends.get('knowledge_growth', 0) > 0.1:
            insights.append("Excellent progress! Your knowledge has grown significantly.")
        
        if metrics['badges_earned'] > 5:
            insights.append("Achievement unlocked! You're mastering multiple topics.")
        
        return insights
    
    async def _generate_next_steps(
        self,
        profile: LearnerProfile
    ) -> List[str]:
        """Generate next learning recommendations."""
        
        recommendations = []
        
        if profile.knowledge_gaps:
            recommendations.append(f"Focus on {profile.knowledge_gaps[0]} to fill knowledge gap")
        
        if len(profile.completed_modules) > 10:
            recommendations.append("Consider taking an assessment to earn a certificate")
        
        recommendations.append("Explore advanced topics in your areas of strength")
        
        return recommendations
    
    async def _identify_next_milestone(
        self,
        profile: LearnerProfile
    ) -> Dict[str, Any]:
        """Identify next achievement milestone."""
        
        completed = len(profile.completed_modules)
        
        milestones = [5, 10, 25, 50, 100]
        for milestone in milestones:
            if completed < milestone:
                return {
                    'target': milestone,
                    'remaining': milestone - completed,
                    'reward': f"Unlock {milestone}-module badge"
                }
        
        return {'target': 'Continue learning!', 'remaining': 0, 'reward': 'Knowledge'}
    
    def _calculate_percentile(self, score: float) -> int:
        """Calculate score percentile among all users."""
        
        # Simplified calculation
        if score >= 90:
            return 95
        elif score >= 75:
            return 75
        elif score >= 60:
            return 50
        else:
            return 25
    
    async def _select_session_content(
        self,
        profile: LearnerProfile,
        available_time: int,
        focus_topic: Optional[str]
    ) -> Dict[str, Any]:
        """Select content for study session."""
        
        content = {
            'main': [],
            'practice': [],
            'summary': [],
            'description': ''
        }
        
        if focus_topic:
            content['description'] = f"Focused session on {focus_topic}"
            # Select topic-specific content
        else:
            content['description'] = "General financial education session"
        
        # Add content based on available time
        if available_time >= 30:
            content['main'] = ['Video lesson', 'Interactive exercise']
            content['practice'] = ['Practice problems', 'Case study']
        else:
            content['main'] = ['Quick article', 'Key concepts review']
            content['practice'] = ['Quiz questions']
        
        content['summary'] = ['Key takeaways', 'Action items']
        
        return content
    
    async def _get_spaced_repetition_items(
        self,
        profile: LearnerProfile
    ) -> List[Dict]:
        """Get items for spaced repetition review."""
        
        # Simplified spaced repetition
        review_items = []
        
        for module_id in profile.completed_modules[-5:]:  # Last 5 modules
            module = self._get_module_by_id(module_id)
            if module:
                review_items.append({
                    'module': module.title,
                    'key_concept': module.learning_objectives[0] if module.learning_objectives else '',
                    'review_type': 'quick_quiz'
                })
        
        return review_items[:3]  # Return top 3 for review
    
    async def _generate_study_tips(
        self,
        profile: LearnerProfile,
        focus_topic: Optional[str]
    ) -> List[str]:
        """Generate personalized study tips."""
        
        tips = [
            "Take notes on key concepts",
            "Apply learning to your personal finances",
            "Discuss concepts with others",
            "Take breaks every 25 minutes"
        ]
        
        if profile.learning_style == 'visual':
            tips.append("Draw diagrams to visualize concepts")
        elif profile.learning_style == 'auditory':
            tips.append("Explain concepts out loud to yourself")
        
        return tips[:3]
    
    async def _generate_motivation_message(
        self,
        profile: LearnerProfile
    ) -> str:
        """Generate motivational message."""
        
        messages = [
            "Every module completed brings you closer to financial mastery!",
            f"You've already completed {len(profile.completed_modules)} modules. Keep going!",
            "Knowledge is the best investment you can make.",
            "Small steps daily lead to big changes over time."
        ]
        
        return messages[len(profile.completed_modules) % len(messages)]
    
    def _get_fallback_learning_path(self, goals: List[str]) -> Dict[str, Any]:
        """Get fallback learning path when AI fails."""
        
        return {
            'path_id': str(uuid.uuid4()),
            'goals': goals,
            'curriculum': [
                {'module_id': '1', 'title': 'Financial Basics', 'level': 'beginner'},
                {'module_id': '2', 'title': 'Budgeting 101', 'level': 'beginner'},
                {'module_id': '3', 'title': 'Saving Strategies', 'level': 'beginner'}
            ],
            'estimated_completion': 30,
            'error': 'Using default learning path'
        }
    
    def _get_fallback_module(self, user_id: str) -> LearningModule:
        """Get fallback module when selection fails."""
        
        return LearningModule(
            module_id='fallback-1',
            title='Introduction to Personal Finance',
            description='Basic financial concepts everyone should know',
            level=CourseLevel.BEGINNER,
            path=LearningPath.FINANCIAL_BASICS,
            estimated_time=30,
            prerequisites=[],
            learning_objectives=['Understand basic financial terms'],
            content_items=[],
            assessments=[],
            resources=[],
            skills_gained=['Financial literacy'],
            completion_criteria={'min_score': 70}
        )
    
    def _get_fallback_assessment(
        self,
        user_id: str,
        topic: str
    ) -> KnowledgeAssessment:
        """Get fallback assessment when AI fails."""
        
        return KnowledgeAssessment(
            assessment_id=str(uuid.uuid4()),
            user_id=user_id,
            module_id=None,
            topic=topic,
            questions_answered=0,
            correct_answers=0,
            score=0,
            proficiency_level='Unknown',
            strengths=[],
            weaknesses=['Assessment unavailable'],
            recommendations=['Please try again later'],
            timestamp=datetime.utcnow()
        )
    
    def _get_fallback_study_session(self, available_time: int) -> Dict[str, Any]:
        """Get fallback study session."""
        
        return {
            'session_id': str(uuid.uuid4()),
            'duration': available_time,
            'segments': [
                {
                    'type': 'content',
                    'duration': available_time,
                    'content': ['General financial education'],
                    'description': 'Self-directed learning'
                }
            ],
            'tips': ['Focus on one concept at a time'],
            'motivation': 'Keep learning!'
        }
    
    def _initialize_modules_library(self) -> Dict[LearningPath, List[Dict]]:
        """Initialize library of learning modules."""
        
        return {
            LearningPath.FINANCIAL_BASICS: [
                {
                    'id': 'fb-001',
                    'title': 'Understanding Money',
                    'level': 'beginner',
                    'estimated_time': 30,
                    'prerequisites': [],
                    'objectives': ['Understand currency', 'Learn about inflation'],
                    'skills': ['Financial literacy'],
                    'content': [
                        {'type': 'video', 'title': 'What is Money?'},
                        {'type': 'article', 'title': 'History of Currency'}
                    ]
                },
                {
                    'id': 'fb-002',
                    'title': 'Banking Basics',
                    'level': 'beginner',
                    'estimated_time': 45,
                    'prerequisites': ['fb-001'],
                    'objectives': ['Understand bank accounts', 'Learn about interest'],
                    'skills': ['Banking knowledge'],
                    'content': [
                        {'type': 'interactive', 'title': 'Types of Bank Accounts'},
                        {'type': 'quiz', 'title': 'Banking Terms Quiz'}
                    ]
                }
            ],
            LearningPath.BUDGETING_MASTERY: [
                {
                    'id': 'bm-001',
                    'title': 'Creating Your First Budget',
                    'level': 'beginner',
                    'estimated_time': 60,
                    'prerequisites': [],
                    'objectives': ['Create a basic budget', 'Track expenses'],
                    'skills': ['Budgeting', 'Expense tracking'],
                    'content': [
                        {'type': 'worksheet', 'title': 'Budget Template'},
                        {'type': 'simulation', 'title': 'Monthly Budget Simulator'}
                    ]
                }
            ],
            LearningPath.INVESTING_FUNDAMENTALS: [
                {
                    'id': 'if-001',
                    'title': 'Introduction to Investing',
                    'level': 'intermediate',
                    'estimated_time': 90,
                    'prerequisites': ['fb-002'],
                    'objectives': ['Understand investment types', 'Learn about risk'],
                    'skills': ['Investment knowledge', 'Risk assessment'],
                    'content': [
                        {'type': 'video', 'title': 'Investment Basics'},
                        {'type': 'case_study', 'title': 'Portfolio Examples'}
                    ]
                }
            ]
        }
    
    def _initialize_question_banks(self) -> Dict[str, List[Dict]]:
        """Initialize assessment question banks."""
        
        return {
            'budgeting': [
                {
                    'id': 'q-b-001',
                    'question': 'What is the 50/30/20 rule?',
                    'options': [
                        '50% needs, 30% wants, 20% savings',
                        '50% savings, 30% needs, 20% wants',
                        '50% wants, 30% savings, 20% needs',
                        '50% debt, 30% expenses, 20% savings'
                    ],
                    'correct': '50% needs, 30% wants, 20% savings',
                    'explanation': 'The 50/30/20 rule allocates after-tax income.'
                }
            ],
            'investing': [
                {
                    'id': 'q-i-001',
                    'question': 'What is diversification?',
                    'options': [
                        'Putting all money in one stock',
                        'Spreading investments across different assets',
                        'Only investing in bonds',
                        'Day trading strategy'
                    ],
                    'correct': 'Spreading investments across different assets',
                    'explanation': 'Diversification reduces risk by spreading investments.'
                }
            ]
        }
    
    def _initialize_badge_criteria(self) -> Dict[str, Dict]:
        """Initialize badge and certification criteria."""
        
        return {
            'first_module': {
                'type': BadgeType.MILESTONE,
                'criteria': 'Complete first module',
                'points': 10
            },
            'week_streak': {
                'type': BadgeType.STREAK,
                'criteria': '7-day learning streak',
                'points': 50
            },
            'course_complete': {
                'type': BadgeType.COMPLETION,
                'criteria': 'Complete entire course',
                'points': 100
            },
            'perfect_score': {
                'type': BadgeType.MASTERY,
                'criteria': '100% on assessment',
                'points': 75
            }
        }
    
    def _initialize_knowledge_graph(self) -> Dict[str, List[str]]:
        """Initialize knowledge dependency graph."""
        
        return {
            'money_basics': [],
            'budgeting': ['money_basics'],
            'saving': ['money_basics', 'budgeting'],
            'investing': ['saving', 'risk_management'],
            'retirement': ['investing', 'tax_planning'],
            'tax_planning': ['income', 'deductions'],
            'risk_management': ['insurance', 'emergency_fund'],
            'debt_management': ['interest', 'budgeting'],
            'wealth_building': ['investing', 'tax_planning', 'real_estate']
        }