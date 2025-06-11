#!/usr/bin/env python3
"""
Performance Testing Suite for Screenshot Monitoring Tool

This script benchmarks various performance-critical operations to validate 
optimizations and track performance improvements over time.

Usage:
    python performance_tests.py                    # Run all benchmarks
    python performance_tests.py --prompt-only      # Test prompt caching only
    python performance_tests.py --config-only      # Test config caching only
    python performance_tests.py --save-results     # Save results to file
"""

import argparse
import json
import time
import statistics
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Import the screenshot monitor
from screenshot_monitor import ScreenshotMonitor


class PerformanceBenchmark:
    """Performance benchmarking utilities"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {}
        }
    
    def time_function(self, func, iterations=1000, warmup=100):
        """Time a function execution over multiple iterations"""
        # Warmup runs
        for _ in range(warmup):
            func()
        
        # Actual timing runs
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            "iterations": iterations,
            "avg_time": statistics.mean(times),
            "median_time": statistics.median(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0.0,
            "total_time": sum(times)
        }
    
    def compare_implementations(self, old_func, new_func, name, iterations=1000):
        """Compare two implementations and calculate improvement ratio"""
        print(f"\n🔬 Benchmarking: {name}")
        print("-" * 60)
        
        old_results = self.time_function(old_func, iterations)
        new_results = self.time_function(new_func, iterations)
        
        improvement_ratio = old_results["avg_time"] / new_results["avg_time"] if new_results["avg_time"] > 0 else float('inf')
        
        print(f"Old implementation: {old_results['avg_time']:.6f}s avg ({old_results['total_time']:.6f}s total)")
        print(f"New implementation: {new_results['avg_time']:.6f}s avg ({new_results['total_time']:.6f}s total)")
        print(f"Performance improvement: {improvement_ratio:.2f}x faster")
        
        self.results["benchmarks"][name] = {
            "old": old_results,
            "new": new_results,
            "improvement_ratio": improvement_ratio,
            "improvement_percentage": ((improvement_ratio - 1) * 100) if improvement_ratio > 1 else 0
        }
        
        return improvement_ratio


class PromptCachingBenchmark(PerformanceBenchmark):
    """Benchmark prompt caching optimization"""
    
    def __init__(self):
        super().__init__()
        self.test_url = "https://example.com/test"
    
    def old_prompt_construction(self):
        """Simulate the old f-string construction method"""
        prompt = f"""You are a website monitoring expert analyzing screenshots for changes. I will provide you with two screenshots of the same website URL: {self.test_url}

The first image is the BASELINE (reference) screenshot.
The second image is the CURRENT screenshot taken more recently.

Please analyze these screenshots and provide a detailed comparison report in the following JSON format:

{{
    "has_changes": true/false,
    "severity": "none|minor|moderate|major|critical",
    "summary": "Brief summary of changes found",
    "changes_detected": [
        {{
            "type": "layout|content|styling|functionality|error|availability",
            "description": "Detailed description of the change",
            "location": "Where on the page this change occurs",
            "impact": "Potential impact of this change"
        }}
    ],
    "availability_status": "available|partially_available|unavailable|error",
    "recommendations": ["List of recommended actions if any issues found"]
}}

Focus on:
- Layout changes (elements moved, resized, disappeared)
- Content changes (text differences, images changed)
- Error messages or broken elements
- Overall site availability and functionality
- Visual styling changes
- Any elements that appear broken or missing

Be thorough but practical - highlight changes that would matter for deployment monitoring."""
        return len(prompt)  # Return something to prevent optimization
    
    def new_prompt_construction(self):
        """Use the new cached template method"""
        template = ScreenshotMonitor._ANALYSIS_PROMPT_TEMPLATE
        prompt = template.format(url=self.test_url)
        return len(prompt)  # Return something to prevent optimization
    
    def run_benchmark(self):
        """Run the prompt caching benchmark"""
        return self.compare_implementations(
            self.old_prompt_construction,
            self.new_prompt_construction,
            "Prompt Construction (String vs Template)",
            iterations=1000
        )


class ModelConfigCachingBenchmark(PerformanceBenchmark):
    """Benchmark model configuration caching optimization"""
    
    def __init__(self):
        super().__init__()
        self.config_file = "models.json"
    
    def old_config_loading(self):
        """Simulate old method: read file every time"""
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            return len(config)
        return 0
    
    def new_config_loading(self):
        """Use the new cached configuration method"""
        # This uses the actual caching implementation
        config = ScreenshotMonitor._config_cache.get(self.config_file)
        if config is None:
            # Would load and cache in real implementation
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                ScreenshotMonitor._config_cache[self.config_file] = config
        return len(config) if config else 0
    
    def run_benchmark(self):
        """Run the model config caching benchmark"""
        # Ensure cache is populated first
        self.new_config_loading()
        
        return self.compare_implementations(
            self.old_config_loading,
            self.new_config_loading,
            "Model Config Loading (File I/O vs Cache)",
            iterations=500
        )


class MemoryUsageBenchmark(PerformanceBenchmark):
    """Benchmark memory usage patterns"""
    
    def __init__(self):
        super().__init__()
    
    def simulate_large_string_creation(self):
        """Simulate creating large strings repeatedly"""
        test_strings = []
        for i in range(10):
            large_string = f"This is a test string number {i} " * 100
            test_strings.append(large_string)
        return len(test_strings)
    
    def simulate_template_reuse(self):
        """Simulate reusing a template"""
        template = "This is a test string number {number} " * 100
        test_strings = []
        for i in range(10):
            formatted = template.format(number=i)
            test_strings.append(formatted)
        return len(test_strings)
    
    def run_benchmark(self):
        """Run memory usage benchmark"""
        return self.compare_implementations(
            self.simulate_large_string_creation,
            self.simulate_template_reuse,
            "Memory Allocation (String Creation vs Template Reuse)",
            iterations=500
        )


class PerformanceTestSuite:
    """Main performance test suite"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "optimizations": {},
            "summary": {}
        }
    
    def run_prompt_benchmark(self):
        """Run prompt caching benchmark"""
        print("=" * 80)
        print("🚀 PROMPT CACHING OPTIMIZATION BENCHMARK")
        print("=" * 80)
        
        benchmark = PromptCachingBenchmark()
        improvement = benchmark.run_benchmark()
        
        self.results["optimizations"]["prompt_caching"] = benchmark.results["benchmarks"]
        return improvement
    
    def run_config_benchmark(self):
        """Run model configuration caching benchmark"""
        print("\n" + "=" * 80)
        print("⚡ MODEL CONFIG CACHING OPTIMIZATION BENCHMARK")
        print("=" * 80)
        
        benchmark = ModelConfigCachingBenchmark()
        improvement = benchmark.run_benchmark()
        
        self.results["optimizations"]["config_caching"] = benchmark.results["benchmarks"]
        return improvement
    
    def run_memory_benchmark(self):
        """Run memory usage benchmark"""
        print("\n" + "=" * 80)
        print("🧠 MEMORY USAGE OPTIMIZATION BENCHMARK")
        print("=" * 80)
        
        benchmark = MemoryUsageBenchmark()
        improvement = benchmark.run_benchmark()
        
        self.results["optimizations"]["memory_usage"] = benchmark.results["benchmarks"]
        return improvement
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("🔬 Screenshot Monitoring Tool - Performance Benchmark Suite")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        improvements = {}
        
        try:
            improvements["prompt"] = self.run_prompt_benchmark()
        except Exception as e:
            print(f"❌ Prompt benchmark failed: {e}")
            improvements["prompt"] = 0
        
        try:
            improvements["config"] = self.run_config_benchmark()
        except Exception as e:
            print(f"❌ Config benchmark failed: {e}")
            improvements["config"] = 0
        
        try:
            improvements["memory"] = self.run_memory_benchmark()
        except Exception as e:
            print(f"❌ Memory benchmark failed: {e}")
            improvements["memory"] = 0
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 80)
        
        total_improvements = 0
        valid_improvements = 0
        
        for name, improvement in improvements.items():
            if improvement > 0:
                print(f"✅ {name.title()}: {improvement:.2f}x faster")
                total_improvements += improvement
                valid_improvements += 1
            else:
                print(f"⚠️  {name.title()}: No improvement measured")
        
        if valid_improvements > 0:
            avg_improvement = total_improvements / valid_improvements
            print(f"\n🎯 Average Performance Improvement: {avg_improvement:.2f}x")
        else:
            print(f"\n⚠️  No performance improvements measured")
        
        self.results["summary"] = {
            "total_benchmarks": len(improvements),
            "successful_benchmarks": valid_improvements,
            "average_improvement": avg_improvement if valid_improvements > 0 else 0,
            "individual_improvements": improvements
        }
        
        return self.results
    
    def save_results(self, filename=None):
        """Save benchmark results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_results_{timestamp}.json"
        
        results_dir = Path("performance_results")
        results_dir.mkdir(exist_ok=True)
        
        filepath = results_dir / filename
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filepath}")
        return filepath


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Performance benchmark suite for screenshot monitoring tool"
    )
    parser.add_argument("--prompt-only", action="store_true", 
                       help="Run only prompt caching benchmark")
    parser.add_argument("--config-only", action="store_true",
                       help="Run only config caching benchmark")
    parser.add_argument("--memory-only", action="store_true",
                       help="Run only memory usage benchmark")
    parser.add_argument("--save-results", action="store_true",
                       help="Save results to JSON file")
    parser.add_argument("--output", type=str,
                       help="Output filename for results")
    
    args = parser.parse_args()
    
    suite = PerformanceTestSuite()
    
    if args.prompt_only:
        suite.run_prompt_benchmark()
    elif args.config_only:
        suite.run_config_benchmark()
    elif args.memory_only:
        suite.run_memory_benchmark()
    else:
        suite.run_all_benchmarks()
    
    if args.save_results or args.output:
        suite.save_results(args.output)


if __name__ == "__main__":
    main() 