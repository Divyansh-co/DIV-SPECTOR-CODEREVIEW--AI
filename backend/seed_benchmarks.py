"""
Seed script to run the benchmark evaluation suite and persist baseline metrics.
Author: Divyansh Mishra
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.database import init_db
from app.evaluation.evaluator import BenchmarkEvaluator

async def main():
    print("=" * 65)
    print("  SPECTER AI CODE REVIEW ENGINE - BENCHMARK SEEDER")
    print("  Engineered by Divyansh Mishra")
    print("=" * 65)
    
    print("\n[1/3] Initializing database...")
    await init_db()
    print("[OK] SQLite database initialized.")

    print("\n[2/3] Executing benchmark evaluation across 12 test cases...")
    evaluator = BenchmarkEvaluator()
    report = await evaluator.run_evaluation()

    print("\n[3/3] Benchmark Results:")
    print("-" * 65)
    print(f"Total Cases:     {report.total_cases}")
    print(f"True Positives:  {report.true_positives}")
    print(f"False Positives: {report.false_positives}")
    print(f"False Negatives: {report.false_negatives}")
    print(f"PRECISION:       {report.precision * 100:.1f}%")
    print(f"RECALL:          {report.recall * 100:.1f}%")
    print(f"F1 SCORE:        {report.f1_score * 100:.1f}%")
    print("-" * 65)
    print("Category Breakdown:")
    for cat, stats in report.category_metrics.items():
        print(f"  * {cat.upper():15s} | Prec: {stats['precision']*100:.1f}% | Rec: {stats['recall']*100:.1f}% | F1: {stats['f1_score']*100:.1f}%")
    print("=" * 65)
    print("[OK] Benchmark dataset successfully seeded into database.")

if __name__ == "__main__":
    asyncio.run(main())
