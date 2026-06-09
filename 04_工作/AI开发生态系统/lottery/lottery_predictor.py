#!/usr/bin/env python3
"""
六肖预测器 - 排名法贝叶斯预测
============================

特征:
- gap: 遗漏期数 (越大越该出)
- recent3/5/10/20/30: 近N期出现次数
- streak: 连续出现次数

算法: 排名法 (避免异常值影响)
1. 每个特征转成排名 0-11
2. 加权求和
3. 选排名前6
"""

import json
from typing import Dict, List, Optional, Tuple
from collections import Counter


class LotteryPredictor:
    """六肖预测器"""

    # 特征权重
    WEIGHTS = {
        'gap': 2.5,
        'recent3': 1.0,
        'recent5': 1.5,
        'recent10': 1.5,
        'recent20': 0.0,
        'recent30': 1.0,
        'streak': 0.3,
    }

    DATA_FILE = '/home/admin1/liuhecai_data.json'

    def __init__(self):
        self.zodiacs = ['龍', '鼠', '牛', '虎', '兔', '蛇', '馬', '羊', '猴', '雞', '狗', '豬']
        self.records = []
        self.last_result = None

    def load_data(self) -> List[Dict]:
        """加载开奖数据"""
        with open(self.DATA_FILE) as f:
            raw = json.load(f)

        self.records = []
        for r in raw:
            if len(r.get('开奖号码', [])) >= 7:
                self.records.append({
                    '期号': r['期号'],
                    '特码': r['特码生肖'],
                    '特码号': r.get('特码号码', ''),
                    '波色': r.get('波色', ''),
                })

        return self.records

    def build_cache(self, records: List[Dict], upto: int) -> Dict[str, Dict]:
        """
        构建特征缓存

        Args:
            records: 开奖记录
            upto: 截至位置(不包含)

        Returns:
            {生肖: {特征: 值}}
        """
        cache = {}
        subset = records[:upto]

        for z in self.zodiacs:
            # 出现位置
            positions = [i for i, r in enumerate(subset) if r['特码'] == z]

            # gap: 距上次出现的遗漏期数
            last_gap = upto - positions[-1] - 1 if positions else 999

            # avg_gap: 平均间隔
            if len(positions) >= 2:
                gaps = [positions[i+1] - positions[i] - 1 for i in range(len(positions)-1)]
                avg_gap = sum(gaps) / len(gaps)
            else:
                avg_gap = 12.0

            # recent N: 近N期出现次数
            recent3 = sum(1 for i in range(max(0, upto-3), upto) if subset[i]['特码'] == z)
            recent5 = sum(1 for i in range(max(0, upto-5), upto) if subset[i]['特码'] == z)
            recent10 = sum(1 for i in range(max(0, upto-10), upto) if subset[i]['特码'] == z)
            recent20 = sum(1 for i in range(max(0, upto-20), upto) if subset[i]['特码'] == z)
            recent30 = sum(1 for i in range(max(0, upto-30), upto) if subset[i]['特码'] == z)

            # streak: 连续出现次数(从后往前数)
            streak = 0
            for i in range(upto-1, -1, -1):
                if subset[i]['特码'] == z:
                    streak += 1
                else:
                    break

            # freq_12: 12期频率
            freq_12 = sum(1 for i in range(max(0, upto-12), upto) if subset[i]['特码'] == z) / min(12, upto)

            cache[z] = {
                'gap': last_gap,
                'avg_gap': avg_gap,
                'recent3': recent3,
                'recent5': recent5,
                'recent10': recent10,
                'recent20': recent20,
                'recent30': recent30,
                'streak': streak,
                'freq_12': freq_12,
                'positions': positions,
            }

        return cache

    def rank_scoring(self, cache: Dict[str, Dict], weights: Dict[str, float]) -> Dict[str, float]:
        """
        排名法评分

        每个特征转成排名(0-11)，加权求和
        gap越大排名越前(遗漏久该出了)
        其他特征也是越大排名越前
        """
        features = list(weights.keys())
        ranks = {z: {f: 0 for f in features} for z in cache.keys()}

        # 对每个特征进行排名
        for f in features:
            vals = [(z, cache[z][f]) for z in cache.keys()]
            vals.sort(key=lambda x: x[1], reverse=True)  # 降序: 大的排名考前

            for i, (z, _) in enumerate(vals):
                ranks[z][f] = i  # 排名0-11

        # 加权求和
        scores = {}
        for z in cache.keys():
            s = sum(ranks[z][f] * weights[f] for f in features if f in weights)
            scores[z] = s

        return scores

    def predict(self, n_train: Optional[int] = None) -> Dict:
        """
        预测下期特码

        Args:
            n_train: 使用多少期数据训练(默认全部)

        Returns:
            {
                'predict_period': 期号,
                'top6': [生肖],
                'scores': {生肖: 分数},
                'n_train': 训练期数,
                'features': {...}
            }
        """
        if not self.records:
            self.load_data()

        if n_train is None:
            n_train = len(self.records)

        # 构建特征缓存
        cache = self.build_cache(self.records, n_train)

        # 排名评分
        scores = self.rank_scoring(cache, self.WEIGHTS)

        # 排序
        ranked = sorted(self.zodiacs, key=lambda z: scores[z], reverse=True)
        top6 = ranked[:6]

        # 预测期号
        last_period = self.records[n_train-1]['期号'] if n_train > 0 else 'unknown'
        # 期号格式: 2026135 -> 2026136
        predict_period = self._next_period(last_period)

        result = {
            'predict_period': predict_period,
            'top6': top6,
            'scores': {z: round(scores[z], 2) for z in self.zodiacs},
            'n_train': n_train,
            'features': cache,
            'top_zodiac': ranked[0],
            'top_score': round(scores[ranked[0]], 2),
        }

        self.last_result = result
        return result

    def _next_period(self, current: str) -> str:
        """计算下一期号"""
        if current.startswith('20'):
            num = int(current[4:])
            return current[:4] + str(num + 1)
        return str(int(current) + 1) if current.isdigit() else current

    def backtest(self, n_start: int = 50, n_end: int = 400) -> Tuple[int, int]:
        """
        回测验证

        从 n_start 期开始，用前 n 期数据预测第 n+1 期
        统计命中次数

        Returns:
            (命中次数, 总预测次数)
        """
        if not self.records:
            self.load_data()

        hits = 0
        total = 0

        for n in range(n_start, min(n_end, len(self.records) - 1)):
            # 用前n期预测
            result = self.predict(n_train=n)
            top6 = result['top6']

            # 实际第n+1期结果
            actual = self.records[n]['特码']

            # 6肖中1算命中
            if actual in top6:
                hits += 1
            total += 1

        return hits, total

    def get_hit_rate(self, n_start: int = 50, n_end: int = 400) -> float:
        """获取回测命中率"""
        hits, total = self.backtest(n_start, n_end)
        return hits / total if total > 0 else 0.0


if __name__ == '__main__':
    predictor = LotteryPredictor()

    print("=" * 60)
    print("  六肖预测系统 - 排名法")
    print("=" * 60)

    # 加载数据
    records = predictor.load_data()
    print(f"\n数据: {len(records)} 期")
    print(f"最新期: {records[-1]['期号']} - {records[-1]['特码']}")

    # 预测
    result = predictor.predict()
    print(f"\n预测期号: {result['predict_period']}")
    print(f"推荐6肖: {result['top6']}")
    print(f"冠军: {result['top_zodiac']} (分数: {result['top_score']})")

    print("\n分数排行:")
    for z, s in sorted(result['scores'].items(), key=lambda x: x[1], reverse=True):
        marker = " ✅" if z in result['top6'] else ""
        print(f"  {z:4}: {s:6.2f}{marker}")

    # 回测
    print("\n" + "-" * 60)
    print("回测验证 (100期 ~ 400期):")
    hits, total = predictor.backtest(100, 400)
    hit_rate = hits / total if total > 0 else 0
    print(f"  命中: {hits}/{total} = {hit_rate:.1%}")

    print("\n" + "=" * 60)