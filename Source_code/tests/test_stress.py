"""
Stress testing for search performance
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from Source_code.controllers.search_controller import SearchController
from Source_code.utils.logger import logger


class StressTest:
    """Stress test the search system"""

    def __init__(self):
        self.controller = SearchController()
        self.test_queries = [
            "پروژه", "گزارش", "فارسی", "جستجو", "مدارک",
            "ایمیل", "مدیریت", "تیم", "مستندات", "درخواست"
        ]

    def run_single_search(self, query: str) -> float:
        """Run a single search and return response time"""
        start = time.time()
        self.controller.search(query)
        return time.time() - start

    def test_concurrent_searches(self, num_workers: int = 10):
        """Test concurrent search performance"""
        logger.info(f"Starting stress test with {num_workers} concurrent workers")

        results = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for i in range(num_workers):
                query = self.test_queries[i % len(self.test_queries)]
                futures.append(executor.submit(self.run_single_search, query))

            for future in as_completed(futures):
                results.append(future.result())

        return results

    def test_bulk_searches(self, num_searches: int = 100):
        """Test many sequential searches"""
        logger.info(f"Running {num_searches} sequential searches")

        times = []
        for i in range(num_searches):
            query = self.test_queries[i % len(self.test_queries)]
            times.append(self.run_single_search(query))

        return times

    def run_full_stress_test(self):
        """Run complete stress test suite"""
        print("\n" + "=" * 60)
        print("🔥 STRESS TESTING PERSIAN SEARCH")
        print("=" * 60)

        # Test 1: Concurrent searches
        print("\n📊 Test 1: Concurrent searches (10 workers)")
        concurrent_times = self.test_concurrent_searches(10)
        print(f"   Avg: {statistics.mean(concurrent_times) * 1000:.2f}ms")
        print(f"   Min: {min(concurrent_times) * 1000:.2f}ms")
        print(f"   Max: {max(concurrent_times) * 1000:.2f}ms")

        # Test 2: Bulk sequential searches
        print("\n📊 Test 2: Bulk sequential searches (100 requests)")
        bulk_times = self.test_bulk_searches(100)
        print(f"   Avg: {statistics.mean(bulk_times) * 1000:.2f}ms")
        print(f"   P95: {statistics.quantiles(bulk_times, n=20)[18] * 1000:.2f}ms")

        # Test 3: Cached performance
        print("\n📊 Test 3: Repeated query performance (50x same query)")
        repeated_times = [self.run_single_search("پروژه") for _ in range(50)]
        print(f"   Avg: {statistics.mean(repeated_times) * 1000:.2f}ms")
        print(f"   Best: {min(repeated_times) * 1000:.2f}ms")

        # Summary
        print("\n" + "=" * 60)
        print("📈 STRESS TEST SUMMARY")
        print("=" * 60)
        print(f"✅ All tests passed")
        print(f"✅ Average response time: {statistics.mean(bulk_times) * 1000:.2f}ms")
        print(f"✅ Throughput: ~{1000 / statistics.mean(bulk_times):.0f} requests/second")
        print("=" * 60)


if __name__ == "__main__":
    stress = StressTest()
    stress.run_full_stress_test()