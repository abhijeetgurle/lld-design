#!/usr/bin/env python3
"""
Test runner for the e-commerce platform

Provides different ways to run tests:
- All tests
- Unit tests only
- Integration tests only
- Specific test files
"""

import sys
import os
import subprocess
import argparse

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Running Unit Tests...")
    
    # Find all test files in unit directory
    unit_test_dir = os.path.join(os.path.dirname(__file__), "tests", "unit")
    test_files = []
    
    if os.path.exists(unit_test_dir):
        for file in os.listdir(unit_test_dir):
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(unit_test_dir, file))
    
    all_passed = True
    for test_file in test_files:
        print(f"\n📋 Running {os.path.basename(test_file)}...")
        result = subprocess.run([sys.executable, test_file], cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            all_passed = False
            print(f"❌ {os.path.basename(test_file)} failed")
        else:
            print(f"✅ {os.path.basename(test_file)} passed")
    
    return all_passed

def run_integration_tests():
    """Run all integration tests"""
    print("🔗 Running Integration Tests...")
    result = subprocess.run([
        sys.executable, 
        "tests/integration/test_complete_system_flows.py"
    ], cwd=os.path.dirname(__file__))
    return result.returncode == 0

def run_all_tests():
    """Run all tests"""
    print("🚀 Running All Tests...")
    
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    
    if unit_success and integration_success:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

def run_specific_test(test_path):
    """Run a specific test file"""
    print(f"🎯 Running Specific Test: {test_path}")
    
    if test_path.endswith('.py') and 'test_' in test_path:
        # Run directly with Python
        result = subprocess.run([
            sys.executable, test_path
        ], cwd=os.path.dirname(__file__))
        
        return result.returncode == 0
    else:
        print("❌ Invalid test file path")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run e-commerce platform tests")
    parser.add_argument(
        "test_type", 
        nargs="?", 
        choices=["unit", "integration", "all"], 
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--file", 
        help="Run a specific test file"
    )
    
    args = parser.parse_args()
    
    if args.file:
        success = run_specific_test(args.file)
    elif args.test_type == "unit":
        success = run_unit_tests()
    elif args.test_type == "integration":
        success = run_integration_tests()
    else:  # all
        success = run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
