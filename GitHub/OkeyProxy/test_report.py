"""
Test Reporting Module for Selenium Test Automation
Provides classes and functions for tracking test execution and generating reports.
"""

import os
import time
import traceback
from datetime import datetime
from contextlib import contextmanager

class TestStep:
    """Represents a single test step with timing and status information."""
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.start_time = None
        self.end_time = None
        self.status = "NOT_STARTED"
        self.error_message = None
    
    def start(self):
        """Start timing the test step."""
        self.start_time = time.time()
        self.status = "RUNNING"
    
    def complete(self, success=True, error_message=None, stack_trace=None):
        """Complete the test step with success/failure status."""
        self.end_time = time.time()
        self.status = "PASSED" if success else "FAILED"
        self.error_message = error_message
        self.stack_trace = stack_trace
    
    def get_duration(self):
        """Get the duration of the test step in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

class TestCase:
    """Represents a complete test case with multiple steps."""
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.steps = []
        self.start_time = None
        self.end_time = None
        self.status = "NOT_STARTED"
        self.error_message = None
        self.stack_trace = None
    
    def start(self):
        """Start the test case."""
        self.start_time = time.time()
        self.status = "RUNNING"
    
    def complete(self, success=None, error_message=None, stack_trace=None):
        """Complete the test case with success/failure status."""
        self.end_time = time.time()
        
        # If success is explicitly provided, use it
        if success is not None:
            self.status = "PASSED" if success else "FAILED"
        else:
            # Auto-determine status based on step results
            self.status = self._determine_status_from_steps()
        
        self.error_message = error_message
        self.stack_trace = stack_trace
    
    def add_step(self, step):
        """Add a test step to this test case."""
        self.steps.append(step)
    
    def get_duration(self):
        """Get the total duration of the test case in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def get_passed_steps(self):
        """Get the number of passed steps."""
        return sum(1 for step in self.steps if step.status == "PASSED")
    
    def get_failed_steps(self):
        """Get the number of failed steps."""
        return sum(1 for step in self.steps if step.status == "FAILED")
    
    def _determine_status_from_steps(self):
        """Determine test case status based on step results."""
        if not self.steps:
            return "NOT_STARTED"
        
        # Check if any steps failed
        failed_steps = [step for step in self.steps if step.status == "FAILED"]
        if failed_steps:
            return "FAILED"
        
        # Check if all steps passed
        passed_steps = [step for step in self.steps if step.status == "PASSED"]
        if len(passed_steps) == len(self.steps):
            return "PASSED"
        
        # If some steps are still running or not started
        return "RUNNING"
    
    def get_failed_step_details(self):
        """Get details of failed steps for debugging."""
        failed_details = []
        for i, step in enumerate(self.steps):
            if step.status == "FAILED":
                failed_details.append({
                    'step_number': i + 1,
                    'step_name': step.name,
                    'error_message': step.error_message,
                    'stack_trace': step.stack_trace
                })
        return failed_details

class TestReport:
    """Manages test execution reporting and generates reports."""
    
    def __init__(self, report_dir):
        self.report_dir = report_dir
        self.test_cases = []
        self.start_time = None
        self.end_time = None
        self.execution_errors = []
    
    def start(self):
        """Start the test report."""
        self.start_time = time.time()
    
    def complete(self):
        """Complete the test report."""
        self.end_time = time.time()
    
    def add_test_case(self, test_case):
        """Add a test case to the report."""
        self.test_cases.append(test_case)
    
    def add_execution_error(self, error_message, stack_trace=None):
        """Add an execution error to the report."""
        self.execution_errors.append({
            'message': error_message,
            'stack_trace': stack_trace,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def get_summary(self):
        """Get a summary of all test results."""
        total_tests = len(self.test_cases)
        passed_tests = sum(1 for tc in self.test_cases if tc.status == "PASSED")
        failed_tests = sum(1 for tc in self.test_cases if tc.status == "FAILED")
        
        total_steps = sum(len(tc.steps) for tc in self.test_cases)
        passed_steps = sum(tc.get_passed_steps() for tc in self.test_cases)
        failed_steps = sum(tc.get_failed_steps() for tc in self.test_cases)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "duration": self.get_duration(),
            "execution_errors": len(self.execution_errors)
        }
    
    def get_duration(self):
        """Get the total duration of all tests in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def generate_html_report(self, filename="test_report"):
        """Generate an HTML report of the test results."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .test-case {{ border: 1px solid #ddd; margin: 10px 0; border-radius: 5px; }}
        .test-case-header {{ background-color: #f9f9f9; padding: 10px; border-bottom: 1px solid #ddd; }}
        .test-step {{ margin: 5px 10px; padding: 5px; border-left: 3px solid #ddd; }}
        .passed {{ border-left-color: #4CAF50; }}
        .failed {{ border-left-color: #f44336; }}
        .running {{ border-left-color: #2196F3; }}
        .not-started {{ border-left-color: #9E9E9E; }}
        .error-details {{ background-color: #ffebee; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .stack-trace {{ background-color: #f5f5f5; padding: 10px; margin: 5px 0; font-family: monospace; font-size: 12px; white-space: pre-wrap; }}
        .execution-errors {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Execution Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        # Add summary
        summary = self.get_summary()
        duration_str = f"{summary['duration']:.2f}" if summary['duration'] is not None else "N/A"
        html_content += f"""
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {summary['total_tests']}</p>
        <p><strong>Passed:</strong> {summary['passed_tests']}</p>
        <p><strong>Failed:</strong> {summary['failed_tests']}</p>
        <p><strong>Total Steps:</strong> {summary['total_steps']}</p>
        <p><strong>Passed Steps:</strong> {summary['passed_steps']}</p>
        <p><strong>Failed Steps:</strong> {summary['failed_steps']}</p>
        <p><strong>Duration:</strong> {duration_str} seconds</p>
        <p><strong>Execution Errors:</strong> {summary['execution_errors']}</p>
    </div>
"""
        
        # Add execution errors if any
        if self.execution_errors:
            html_content += """
    <div class="execution-errors">
        <h2>Execution Errors</h2>
"""
            for error in self.execution_errors:
                html_content += f"""
        <div class="error-details">
            <p><strong>Time:</strong> {error['timestamp']}</p>
            <p><strong>Error:</strong> {error['message']}</p>
"""
                if error['stack_trace']:
                    html_content += f"""
            <div class="stack-trace">{error['stack_trace']}</div>
"""
                html_content += "</div>"
            html_content += "</div>"
        
        # Add test cases
        for test_case in self.test_cases:
            status_class = test_case.status.lower()
            duration_str = f"{test_case.get_duration():.2f}" if test_case.get_duration() is not None else "N/A"
            html_content += f"""
    <div class="test-case">
        <div class="test-case-header">
            <h3>{test_case.name}</h3>
            <p><strong>Status:</strong> {test_case.status}</p>
            <p><strong>Description:</strong> {test_case.description}</p>
            <p><strong>Duration:</strong> {duration_str} seconds</p>
"""
            
            # Add test case error details if any
            if test_case.error_message:
                html_content += f"""
            <div class="error-details">
                <p><strong>Test Case Error:</strong> {test_case.error_message}</p>
"""
                if test_case.stack_trace:
                    html_content += f"""
                <div class="stack-trace">{test_case.stack_trace}</div>
"""
                html_content += "</div>"
            
            html_content += "</div>"
            
            for step in test_case.steps:
                step_class = step.status.lower().replace('_', '-')
                duration_str = f"{step.get_duration():.2f}" if step.get_duration() is not None else "N/A"
                html_content += f"""
        <div class="test-step {step_class}">
            <p><strong>{step.name}</strong> - {step.description}</p>
            <p>Status: {step.status}</p>
            <p>Duration: {duration_str} seconds</p>
"""
                if step.error_message:
                    html_content += f"""
            <div class="error-details">
                <p><strong>Step Error:</strong> {step.error_message}</p>
"""
                    if step.stack_trace:
                        html_content += f"""
                <div class="stack-trace">{step.stack_trace}</div>
"""
                    html_content += "</div>"
                html_content += "</div>"
            
            html_content += "</div>"
        
        html_content += """
</body>
</html>
"""
        
        # Write to file
        report_file = os.path.join(self.report_dir, f"{filename}.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_file

    def generate_text_report(self, console_output="", filename="test_report"):
        """Generate a text report with console output format."""
        report_content = f"""
Test Execution Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{console_output}

============================================================
FINAL TEST SUMMARY
============================================================
"""
        
        # Add test case results
        for test_case in self.test_cases:
            status_icon = "✓" if test_case.status == "PASSED" else "✗" if test_case.status == "FAILED" else "⚠"
            report_content += f"{status_icon} {test_case.name}: {test_case.status}\n"
            
            # Add error details for failed tests
            if test_case.status == "FAILED":
                if test_case.error_message:
                    report_content += f"   Error: {test_case.error_message}\n"
                failed_steps = test_case.get_failed_step_details()
                if failed_steps:
                    report_content += "   Failed Steps:\n"
                    for step_detail in failed_steps:
                        report_content += f"     Step {step_detail['step_number']}: {step_detail['step_name']}\n"
                        if step_detail['error_message']:
                            report_content += f"       Error: {step_detail['error_message']}\n"
        
        # Add execution errors if any
        if self.execution_errors:
            report_content += "\nExecution Errors:\n"
            for error in self.execution_errors:
                report_content += f"  {error['timestamp']}: {error['message']}\n"
        
        # Add overall results
        summary = self.get_summary()
        passed_count = summary['passed_tests']
        failed_count = summary['failed_tests']
        skipped_count = 0  # Not currently tracked
        total_count = summary['total_tests']
        
        report_content += f"""
Overall Results:
  Passed: {passed_count}
  Failed: {failed_count}
  Skipped: {skipped_count}
  Total: {total_count}

Test reports saved in: {self.report_dir}
"""
        
        # Write to file
        report_file = os.path.join(self.report_dir, f"{filename}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file

def create_test_case(name, description):
    """Create a new test case."""
    return TestCase(name, description)

@contextmanager
def track_step(test_case, step_name, step_description):
    """Context manager for tracking a test step with enhanced error handling."""
    step = TestStep(step_name, step_description)
    test_case.add_step(step)
    step.start()
    
    try:
        yield step
        step.complete(success=True)
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        step.complete(success=False, error_message=error_message, stack_trace=stack_trace)
        print(f"❌ Step '{step_name}' failed: {error_message}")
        print(f"Stack trace: {stack_trace}")
        raise 