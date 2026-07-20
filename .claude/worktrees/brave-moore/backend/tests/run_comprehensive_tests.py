#!/usr/bin/env python3
"""
Comprehensive test runner for Financial Planning System

Runs all test suites with proper sequencing, coverage analysis,
and generates comprehensive reports.

Usage:
    python tests/run_comprehensive_tests.py --suite all
    python tests/run_comprehensive_tests.py --suite unit --coverage
    python tests/run_comprehensive_tests.py --suite financial --validate-accuracy
    python tests/run_comprehensive_tests.py --quick  # Fast subset
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.coverage.test_coverage_analysis import FinancialTestCoverageAnalyzer


class ComprehensiveTestRunner:
    """
    Comprehensive test runner for financial planning system
    
    Orchestrates all test types with proper sequencing and reporting
    """
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.coverage_analyzer = None
        
        # Define test suites
        self.test_suites = {
            'unit': {
                'path': 'tests/unit/',
                'description': 'Unit tests for individual components',
                'required': True,
                'timeout': 300  # 5 minutes
            },
            'property': {
                'path': 'tests/unit/test_financial_property_based.py',
                'description': 'Property-based tests with Hypothesis',
                'required': True,
                'timeout': 600  # 10 minutes
            },
            'integration': {
                'path': 'tests/integration/',
                'description': 'Integration tests for API endpoints',
                'required': True,
                'timeout': 900  # 15 minutes
            },
            'validation': {
                'path': 'tests/validation/',
                'description': 'Financial accuracy validation tests',
                'required': True,
                'timeout': 300  # 5 minutes
            },
            'backtesting': {
                'path': 'tests/backtesting/',
                'description': 'Strategy backtesting framework',
                'required': False,  # Optional due to data dependencies
                'timeout': 1800  # 30 minutes
            },
            'performance': {
                'path': 'tests/performance/',
                'description': 'Performance and benchmark tests',
                'required': False,  # Resource intensive
                'timeout': 600  # 10 minutes
            }
        }
        
        # Quick test suite for rapid feedback
        self.quick_tests = [
            'tests/unit/test_monte_carlo_advanced.py::TestAdvancedMonteCarloEngine::test_engine_initialization',
            'tests/unit/test_portfolio_optimization_advanced.py::TestIntelligentPortfolioOptimizer::test_optimizer_initialization',
            'tests/unit/test_tax_optimization_advanced.py::TestTaxOptimizationEngine::test_tax_engine_initialization',
            'tests/validation/test_financial_accuracy_comprehensive.py::TestFinancialFormulaAccuracy::test_present_value_accuracy',
            'tests/integration/test_financial_api_comprehensive.py::TestUserManagementAPI::test_user_registration_flow'
        ]
    
    def run_test_suite(self, suite_name: str, **kwargs) -> Dict:
        """
        Run a specific test suite
        
        Args:
            suite_name: Name of test suite to run
            **kwargs: Additional arguments for pytest
            
        Returns:
            Test results dictionary
        """
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite_config = self.test_suites[suite_name]
        test_path = suite_config['path']
        timeout = suite_config.get('timeout', 300)
        
        print(f"📋 Running {suite_name} tests: {suite_config['description']}")
        
        # Build pytest command
        cmd = [
            'python', '-m', 'pytest',
            test_path,
            '-v',
            '--tb=short',
            f'--timeout={timeout}',
            '--timeout-method=thread'
        ]
        
        # Add coverage if requested
        if kwargs.get('coverage', False):
            cmd.extend([
                '--cov=app',
                '--cov-report=xml',
                '--cov-report=html:htmlcov',
                '--cov-report=term-missing'
            ])
        
        # Add markers
        if kwargs.get('exclude_slow', False):
            cmd.extend(['-m', 'not slow'])
        
        if kwargs.get('only_fast', False):
            cmd.extend(['-m', 'not slow and not external'])
        
        # Add parallel execution
        if kwargs.get('parallel', False):
            cmd.extend(['-n', 'auto'])
        
        # Add junit XML output
        cmd.extend(['--junitxml=test-results.xml'])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60  # Add buffer time
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            test_results = {
                'suite': suite_name,
                'success': result.returncode == 0,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            # Extract test counts from output
            stdout = result.stdout
            if 'passed' in stdout or 'failed' in stdout:
                # Parse pytest summary line
                lines = stdout.split('\n')
                summary_line = next((line for line in lines if 'passed' in line or 'failed' in line), '')
                test_results['summary'] = summary_line.strip()
            
            self.test_results[suite_name] = test_results
            
            if result.returncode == 0:
                print(f"✅ {suite_name} tests passed ({execution_time:.1f}s)")
            else:
                print(f"❌ {suite_name} tests failed ({execution_time:.1f}s)")
                if kwargs.get('verbose', False):
                    print(f"STDOUT:\n{result.stdout}")
                    print(f"STDERR:\n{result.stderr}")
            
            return test_results
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {suite_name} tests timed out after {timeout}s")
            return {
                'suite': suite_name,
                'success': False,
                'execution_time': timeout,
                'error': 'Timeout',
                'timeout': True
            }
        
        except Exception as e:
            print(f"❌ {suite_name} tests failed with error: {e}")
            return {
                'suite': suite_name,
                'success': False,
                'error': str(e),
                'exception': True
            }
    
    def run_quick_tests(self) -> Dict:
        """Run quick subset of tests for rapid feedback"""
        print("🚀 Running quick test suite for rapid feedback")
        
        cmd = [
            'python', '-m', 'pytest',
            *self.quick_tests,
            '-v',
            '--tb=short',
            '--timeout=60'
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            execution_time = time.time() - start_time
            
            success = result.returncode == 0
            
            if success:
                print(f"✅ Quick tests passed ({execution_time:.1f}s)")
            else:
                print(f"❌ Quick tests failed ({execution_time:.1f}s)")
                print("STDERR:", result.stderr)
            
            return {
                'suite': 'quick',
                'success': success,
                'execution_time': execution_time,
                'return_code': result.returncode
            }
        
        except subprocess.TimeoutExpired:
            print("⏰ Quick tests timed out")
            return {'suite': 'quick', 'success': False, 'timeout': True}
    
    def run_coverage_analysis(self, test_suite: str = 'all') -> Dict:
        """Run comprehensive coverage analysis"""
        print("🔍 Running coverage analysis")
        
        if not self.coverage_analyzer:
            self.coverage_analyzer = FinancialTestCoverageAnalyzer()
        
        try:
            coverage_report = self.coverage_analyzer.run_coverage_analysis(test_suite)
            
            # Check if coverage requirements are met
            meets_requirements = self.coverage_analyzer.check_coverage_requirements()
            coverage_report['meets_requirements'] = meets_requirements
            
            overall = coverage_report['overall_coverage']
            print(f"📈 Coverage: {overall['line_coverage_percent']:.1f}% lines, {overall['branch_coverage_percent']:.1f}% branches")
            
            if meets_requirements:
                print("✅ Coverage requirements met")
            else:
                print("❌ Coverage requirements not met")
            
            return coverage_report
            
        except Exception as e:
            print(f"❌ Coverage analysis failed: {e}")
            return {'error': str(e), 'meets_requirements': False}
    
    def validate_financial_accuracy(self) -> Dict:
        """Run financial calculation accuracy validation"""
        print("📊 Validating financial calculation accuracy")
        
        accuracy_tests = [
            'tests/validation/test_financial_accuracy_comprehensive.py',
            'tests/unit/test_financial_property_based.py::TestFinancialCalculationProperties',
        ]
        
        cmd = [
            'python', '-m', 'pytest',
            *accuracy_tests,
            '-v',
            '--tb=short',
            '-x',  # Stop on first failure for accuracy tests
            '--timeout=300'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
            
            success = result.returncode == 0
            
            if success:
                print("✅ Financial accuracy validation passed")
            else:
                print("❌ Financial accuracy validation failed")
                print("Critical financial calculations may be inaccurate!")
            
            return {
                'validation': 'financial_accuracy',
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        
        except Exception as e:
            print(f"❌ Financial accuracy validation error: {e}")
            return {'validation': 'financial_accuracy', 'success': False, 'error': str(e)}
    
    def run_performance_benchmarks(self) -> Dict:
        """Run performance benchmark tests"""
        print("📏 Running performance benchmarks")
        
        benchmark_tests = [
            'tests/performance/test_financial_models_benchmarks.py',
            'tests/unit/test_monte_carlo_advanced.py::TestAdvancedMonteCarloEngine::test_performance_requirements',
            'tests/unit/test_portfolio_optimization_advanced.py::TestIntelligentPortfolioOptimizer::test_performance_requirements'
        ]
        
        cmd = [
            'python', '-m', 'pytest',
            *benchmark_tests,
            '-v',
            '--tb=short',
            '--benchmark-json=benchmark-results.json',
            '--timeout=600'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=700)
            
            success = result.returncode == 0
            
            if success:
                print("✅ Performance benchmarks passed")
            else:
                print("❌ Performance benchmarks failed")
            
            return {
                'benchmark': 'performance',
                'success': success,
                'return_code': result.returncode
            }
        
        except Exception as e:
            print(f"❌ Performance benchmark error: {e}")
            return {'benchmark': 'performance', 'success': False, 'error': str(e)}
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_execution_time': time.time() - self.start_time if self.start_time else 0,
            'test_results': self.test_results,
            'summary': {
                'total_suites': len(self.test_results),
                'passed_suites': sum(1 for r in self.test_results.values() if r.get('success', False)),
                'failed_suites': sum(1 for r in self.test_results.values() if not r.get('success', True))
            }
        }
        
        # Add coverage information if available
        if hasattr(self, 'coverage_report'):
            report['coverage'] = self.coverage_report
        
        # Save report
        with open('comprehensive_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def run_all_tests(self, **kwargs) -> bool:
        """Run all test suites in proper sequence"""
        self.start_time = time.time()
        
        print("🚀 Starting Comprehensive Financial Planning Test Suite")
        print("=" * 60)
        
        success = True
        
        # 1. Quick smoke test first
        if not kwargs.get('skip_quick', False):
            quick_result = self.run_quick_tests()
            if not quick_result.get('success', False):
                print("⚠️  Quick tests failed - continuing with full suite")
        
        # 2. Run core test suites in order
        suite_order = ['unit', 'property', 'validation', 'integration']
        
        for suite_name in suite_order:
            if kwargs.get('suites') and suite_name not in kwargs['suites']:
                continue
            
            result = self.run_test_suite(suite_name, **kwargs)
            if not result.get('success', False):
                success = False
                if self.test_suites[suite_name]['required']:
                    print(f"⚠️  Required test suite {suite_name} failed")
        
        # 3. Run optional suites if requested
        optional_suites = ['backtesting', 'performance']
        for suite_name in optional_suites:
            if kwargs.get('include_optional', False) or (kwargs.get('suites') and suite_name in kwargs['suites']):
                result = self.run_test_suite(suite_name, **kwargs)
                # Don't fail overall if optional tests fail
        
        # 4. Run coverage analysis
        if kwargs.get('coverage', False):
            self.coverage_report = self.run_coverage_analysis()
            if not self.coverage_report.get('meets_requirements', False):
                print("⚠️  Coverage requirements not met")
                # Don't fail build for coverage, but warn
        
        # 5. Validate financial accuracy
        if kwargs.get('validate_accuracy', True):
            accuracy_result = self.validate_financial_accuracy()
            if not accuracy_result.get('success', False):
                print("⚠️  Financial accuracy validation failed")
                success = False  # This is critical
        
        # 6. Performance benchmarks
        if kwargs.get('benchmarks', False):
            benchmark_result = self.run_performance_benchmarks()
            # Don't fail build for performance, but report
        
        # 7. Generate comprehensive report
        report = self.generate_comprehensive_report()
        
        # Summary
        print("\n" + "=" * 60)
        print("📄 Test Suite Summary")
        print(f"   Total execution time: {report['total_execution_time']:.1f}s")
        print(f"   Test suites run: {report['summary']['total_suites']}")
        print(f"   Passed: {report['summary']['passed_suites']}")
        print(f"   Failed: {report['summary']['failed_suites']}")
        
        if success:
            print("✅ All critical tests passed")
        else:
            print("❌ Some critical tests failed")
        
        print(f"\n📁 Detailed report saved to: comprehensive_test_report.json")
        
        return success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Financial Planning System"
    )
    
    parser.add_argument(
        '--suite', 
        choices=['all', 'unit', 'property', 'integration', 'validation', 'backtesting', 'performance', 'quick'],
        default='all',
        help='Test suite to run'
    )
    
    parser.add_argument(
        '--coverage', 
        action='store_true',
        help='Run with coverage analysis'
    )
    
    parser.add_argument(
        '--validate-accuracy', 
        action='store_true',
        default=True,
        help='Run financial accuracy validation'
    )
    
    parser.add_argument(
        '--benchmarks', 
        action='store_true',
        help='Run performance benchmarks'
    )
    
    parser.add_argument(
        '--parallel', 
        action='store_true',
        help='Run tests in parallel'
    )
    
    parser.add_argument(
        '--exclude-slow', 
        action='store_true',
        help='Exclude slow tests'
    )
    
    parser.add_argument(
        '--include-optional', 
        action='store_true',
        help='Include optional test suites'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Run only quick tests for rapid feedback'
    )
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.quick or args.suite == 'quick':
        result = runner.run_quick_tests()
        sys.exit(0 if result.get('success', False) else 1)
    
    # Build kwargs from args
    kwargs = {
        'coverage': args.coverage,
        'validate_accuracy': args.validate_accuracy,
        'benchmarks': args.benchmarks,
        'parallel': args.parallel,
        'exclude_slow': args.exclude_slow,
        'include_optional': args.include_optional,
        'verbose': args.verbose
    }
    
    if args.suite != 'all':
        kwargs['suites'] = [args.suite]
    
    success = runner.run_all_tests(**kwargs)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
