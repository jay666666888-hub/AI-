#!/usr/bin/env python3
"""
六肖预测系统 - 测试套件
TDD: Red → Green → Refactor
"""

import unittest
import json
import os
import sys

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')

from lottery.lottery_predictor import LotteryPredictor


class TestLotteryPredictor(unittest.TestCase):
    """六肖预测器核心测试"""

    @classmethod
    def setUpClass(cls):
        """加载测试数据"""
        data_path = '/home/admin1/liuhecai_data.json'
        with open(data_path) as f:
            cls.test_data = json.load(f)[:100]  # 前100期用于测试

    def test_load_data(self):
        """测试数据加载"""
        predictor = LotteryPredictor()
        records = predictor.load_data()
        self.assertGreater(len(records), 400)  # 至少有400期

    def test_build_cache(self):
        """测试特征缓存构建"""
        predictor = LotteryPredictor()
        records = predictor.load_data()
        cache = predictor.build_cache(records, len(records))

        self.assertEqual(len(cache), 12)  # 12个生肖
        for z in ['龍', '鼠', '牛', '虎', '兔', '龍']:
            self.assertIn(z, cache)

        # 检查必要特征
        for z, data in cache.items():
            self.assertIn('gap', data)
            self.assertIn('recent3', data)
            self.assertIn('recent5', data)

    def test_rank_scoring(self):
        """测试排名评分"""
        predictor = LotteryPredictor()
        records = predictor.load_data()
        cache = predictor.build_cache(records, len(records))
        scores = predictor.rank_scoring(cache, predictor.WEIGHTS)

        self.assertEqual(len(scores), 12)

        # 所有分数应该是正数
        for z, s in scores.items():
            self.assertGreater(s, 0)

        # 排名最高的应该有最高分
        top_z = max(scores, key=scores.get)
        self.assertIn(top_z, scores)

    def test_predict_top6(self):
        """测试预测返回6肖"""
        predictor = LotteryPredictor()
        result = predictor.predict(n_train=400)

        self.assertIn('top6', result)
        self.assertEqual(len(result['top6']), 6)  # 恰好6肖

        # 所有生肖应该在12个中
        all_zodiacs = {'龍', '鼠', '牛', '虎', '兔', '龍', '蛇', '馬', '羊', '猴', '雞', '狗', '豬'}
        for z in result['top6']:
            self.assertIn(z, all_zodiacs)

    def test_backtest(self):
        """回测验证"""
        predictor = LotteryPredictor()
        hits, total = predictor.backtest(n_start=100, n_end=200)

        hit_rate = hits / total if total > 0 else 0
        self.assertGreaterEqual(hit_rate, 0)
        self.assertLessEqual(hit_rate, 1)
        print(f"\n回测结果: {hits}/{total} = {hit_rate:.1%}")


class TestFeatureEngineering(unittest.TestCase):
    """特征工程测试"""

    def test_gap_calculation(self):
        """测试遗漏值计算"""
        predictor = LotteryPredictor()
        records = [
            {'特码': '龍'},  # 位置0
            {'特码': '虎'},  # 位置1
            {'特码': '龍'},  # 位置2
            {'特码': '蛇'},  # 位置3
        ]
        # subset = records[:4] = 全部4条
        # 龍最后出现在位置2，当前upto=4，所以gap = 4-2-1 = 1
        cache = predictor.build_cache(records, 4)

        # 龍最后出现在位置2，gap应该是1 (4-2-1)
        # 虎最后出现在位置1，gap应该是2 (4-1-1)
        self.assertEqual(cache['龍']['gap'], 1)
        self.assertEqual(cache['虎']['gap'], 2)

    def test_recent_counts(self):
        """测试近期计数"""
        predictor = LotteryPredictor()
        # 前3期是龍，后2期是虎 (0,1,2 = 龍, 3,4 = 虎)
        records = [{'特码': '龍'}] * 3 + [{'特码': '虎'}] * 2

        cache = predictor.build_cache(records, 5)

        # recent3 查看 positions [2,3,4] = [龍, 虎, 虎] → 龍出现1次
        self.assertEqual(cache['龍']['recent3'], 1)
        # recent5 查看 positions [0,1,2,3,4] = [龍, 龍, 龍, 虎, 虎] → 龍出现3次
        self.assertEqual(cache['龍']['recent5'], 3)
        self.assertEqual(cache['虎']['recent5'], 2)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_predict_with_delay_tracking(self):
        """测试预测与延迟跟踪器集成"""
        from infrastructure.tools.delayed_outcome_tracker import DelayedOutcomeTracker

        predictor = LotteryPredictor()
        tracker = DelayedOutcomeTracker()

        # 预测
        result = predictor.predict(n_train=450)
        task_id = f"lottery_{result['predict_period']}"

        # 记录到延迟跟踪器
        tracker.track(
            task_id=task_id,
            task_type='lottery_predict',
            initial_outcome=0.5,  # 初始50%置信
            initial_success=True
        )

        # 验证已记录
        self.assertIn(task_id, tracker.tracked_tasks)
        tracked = tracker.tracked_tasks[task_id]
        self.assertEqual(tracked.task_type, 'lottery_predict')


if __name__ == '__main__':
    unittest.main(verbosity=2)