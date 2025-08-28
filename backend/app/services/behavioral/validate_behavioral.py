"""
Simple validation script for Behavioral Finance Analysis System
(No external dependencies required)
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_imports():
    """Validate that the module can be imported"""
    try:
        # Test basic imports without requiring external libraries
        from behavioral_analysis import (
            BehavioralBias,
            NudgeType,
            GoalBucket,
            CommitmentLevel,
            BiasDetection,
            Nudge,
            MentalAccount,
            GoalBasedBucket,
            CommitmentDevice,
            BehavioralProfile
        )
        print("✓ All data classes imported successfully")
        
        # Validate enums
        assert len([b for b in BehavioralBias]) >= 10, "BehavioralBias enum incomplete"
        print(f"✓ BehavioralBias enum has {len([b for b in BehavioralBias])} biases")
        
        assert len([n for n in NudgeType]) >= 10, "NudgeType enum incomplete"
        print(f"✓ NudgeType enum has {len([n for n in NudgeType])} types")
        
        assert len([g for g in GoalBucket]) == 5, "GoalBucket enum should have 5 buckets"
        print(f"✓ GoalBucket enum has {len([g for g in GoalBucket])} buckets")
        
        assert len([c for c in CommitmentLevel]) == 3, "CommitmentLevel enum should have 3 levels"
        print(f"✓ CommitmentLevel enum has {len([c for c in CommitmentLevel])} levels")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False

def validate_dataclasses():
    """Validate dataclass structures"""
    try:
        from behavioral_analysis import (
            BiasDetection,
            Nudge,
            MentalAccount,
            GoalBasedBucket,
            CommitmentDevice,
            BehavioralProfile,
            BehavioralBias,
            NudgeType,
            GoalBucket,
            CommitmentLevel
        )
        
        # Test BiasDetection
        bias = BiasDetection(
            bias_type=BehavioralBias.LOSS_AVERSION,
            severity=0.7,
            confidence=0.8,
            evidence=["Test evidence"],
            impact_on_returns=-0.02,
            recommended_nudges=[]
        )
        assert bias.severity == 0.7
        print("✓ BiasDetection dataclass works correctly")
        
        # Test Nudge
        nudge = Nudge(
            nudge_type=NudgeType.REFRAMING,
            message="Test message",
            action="test_action",
            expected_effectiveness=0.75,
            implementation_difficulty="easy",
            personalization_factors={}
        )
        assert nudge.expected_effectiveness == 0.75
        print("✓ Nudge dataclass works correctly")
        
        # Test MentalAccount
        account = MentalAccount(
            name="Emergency",
            purpose="Emergency fund",
            current_value=10000,
            target_value=20000,
            time_horizon=6,
            risk_tolerance="low",
            assets=["cash"],
            allocation_percentage=0.2,
            behavioral_constraints=[]
        )
        assert account.current_value == 10000
        print("✓ MentalAccount dataclass works correctly")
        
        # Test GoalBasedBucket
        bucket = GoalBasedBucket(
            bucket_type=GoalBucket.SAFETY,
            goal_description="Emergency fund",
            priority=1,
            current_allocation=10000,
            target_allocation=0.2,
            time_horizon=6,
            required_return=0.02,
            risk_budget=0.05,
            assets=[],
            behavioral_guardrails=["No equities"]
        )
        assert bucket.priority == 1
        print("✓ GoalBasedBucket dataclass works correctly")
        
        # Test CommitmentDevice
        device = CommitmentDevice(
            device_id="test_device",
            level=CommitmentLevel.MODERATE,
            description="Test device",
            trigger_conditions=["Condition 1"],
            actions=["Action 1"],
            override_requirements=None,
            effectiveness_score=0.8,
            user_acceptance=0.6
        )
        assert device.effectiveness_score == 0.8
        print("✓ CommitmentDevice dataclass works correctly")
        
        # Test BehavioralProfile
        profile = BehavioralProfile(
            user_id="test_user",
            detected_biases=[bias],
            risk_perception=0.6,
            loss_aversion_coefficient=2.25,
            time_preference=0.8,
            social_influence_sensitivity=0.3,
            cognitive_load_capacity=0.7,
            decision_style="analytical",
            financial_literacy_score=0.75,
            stress_response_pattern="steady",
            preferred_nudge_types=[NudgeType.REFRAMING]
        )
        assert profile.loss_aversion_coefficient == 2.25
        print("✓ BehavioralProfile dataclass works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Dataclass validation error: {e}")
        return False

def validate_analyzer_initialization():
    """Validate BehavioralFinanceAnalyzer can be initialized"""
    try:
        # This will fail if numpy/scipy are not installed
        # But at least validates the class structure
        print("\nAttempting to initialize BehavioralFinanceAnalyzer...")
        print("(This may fail if numpy/scipy/pandas are not installed)")
        
        from behavioral_analysis import BehavioralFinanceAnalyzer
        
        # Try to create instance
        try:
            analyzer = BehavioralFinanceAnalyzer()
            print("✓ BehavioralFinanceAnalyzer initialized successfully")
            
            # Check methods exist
            assert hasattr(analyzer, 'analyze_behavioral_profile')
            assert hasattr(analyzer, 'create_nudge_engine')
            assert hasattr(analyzer, 'optimize_mental_accounting')
            assert hasattr(analyzer, 'create_goal_based_buckets')
            assert hasattr(analyzer, 'implement_commitment_devices')
            assert hasattr(analyzer, 'build_behavioral_portfolio')
            print("✓ All main methods are present")
            
            return True
        except ImportError as e:
            print(f"⚠ Cannot initialize analyzer (missing dependencies): {e}")
            print("  Install with: pip install numpy scipy pandas")
            return False
            
    except Exception as e:
        print(f"✗ Analyzer validation error: {e}")
        return False

def main():
    """Run validation tests"""
    print("=" * 60)
    print("Behavioral Finance Analysis System Validation")
    print("=" * 60)
    
    results = []
    
    print("\n1. Testing imports...")
    results.append(validate_imports())
    
    print("\n2. Testing dataclasses...")
    results.append(validate_dataclasses())
    
    print("\n3. Testing analyzer initialization...")
    results.append(validate_analyzer_initialization())
    
    print("\n" + "=" * 60)
    if all(results[:2]):  # First two tests should pass
        print("✓ Core validation PASSED")
        print("  The behavioral finance module structure is correct.")
        if not results[2]:
            print("  Note: Full functionality requires: pip install numpy scipy pandas")
    else:
        print("✗ Validation FAILED")
        print("  Please check the error messages above.")
    print("=" * 60)

if __name__ == "__main__":
    main()