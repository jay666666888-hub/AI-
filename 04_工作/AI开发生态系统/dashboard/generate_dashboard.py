#!/usr/bin/env python3
"""
Dashboard Generator
生成包含实时数据的 dashboard HTML
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')

def generate_dashboard():
    # 收集数据
    from infrastructure.tools.delayed_outcome_tracker import DelayedOutcomeTracker
    from infrastructure.tools.unified_calibration import UnifiedCalibrationSystem

    tracker = DelayedOutcomeTracker()
    cal = UnifiedCalibrationSystem()

    # ECE数据
    ece_data = {}
    for tt in cal.calibrator.calibrations:
        if cal.calibrator.calibrations[tt].count > 0:
            ece_data[tt] = cal.calibrator.get_ece(tt)

    # 延迟跟踪数据
    delay_data = []
    for tid, t in list(tracker.tracked_tasks.items())[-5:]:
        delay_data.append({
            'id': tid,
            'type': t.task_type,
            'checkpoints': 'T+1h/6h/24h' if 'lottery' in tid else 'T+...'
        })

    # 六肖预测
    lottery_data = {'period': '2026136', 'top6': [], 'scores': {}, 'hitRate': 0.5}
    hermes_data = {'top6': []}

    try:
        with open('/home/admin1/liuhecai_v7_prediction.json') as f:
            p = json.load(f)
            hermes_data['top6'] = p.get('推荐6肖', [])
            hermes_data['period'] = p.get('预测期号', '')
    except:
        pass

    try:
        with open('/mnt/e/黑曜石/04_工作/AI开发生态系统/lottery/lottery_predictor.py') as f:
            pass
        # 尝试导入预测器
        sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统')
        from lottery.lottery_predictor import LotteryPredictor
        predictor = LotteryPredictor()
        predictor.load_data()
        result = predictor.predict()
        lottery_data['top6'] = result['top6']
        lottery_data['scores'] = result['scores']
        lottery_data['period'] = result['predict_period']
        hits, total = predictor.backtest(200, 450)
        lottery_data['hitRate'] = hits / total if total > 0 else 0.5
    except Exception as e:
        print(f"Warning: Could not load lottery predictor: {e}", file=sys.stderr)

    # 计算共同生肖
    common = list(set(lottery_data['top6']) & set(hermes_data['top6'])) if lottery_data['top6'] else []

    # 渲染HTML
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ralph Ecosystem Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }}
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d4ff, #7b2ff7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: #888; font-size: 0.9rem; margin-top: 10px; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .stat-row {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }}
        .stat-value {{ font-size: 1.8rem; font-weight: 700; color: #00d4ff; }}
        .stat-label {{ font-size: 0.75rem; color: #888; margin-top: 5px; }}
        .lottery-card {{
            background: linear-gradient(135deg, rgba(123,47,247,0.15), rgba(0,212,255,0.15));
            text-align: center;
        }}
        .period {{ font-size: 0.9rem; color: #888; }}
        .period-num {{ font-size: 2.2rem; font-weight: 700; color: #00d4ff; margin: 10px 0; }}
        .zodiac-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin: 20px 0;
        }}
        .zodiac-tag {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 1rem;
            background: rgba(0,0,0,0.4);
            transition: all 0.3s;
        }}
        .zodiac-tag.recommended {{
            background: linear-gradient(135deg, #7b2ff7, #00d4ff);
            box-shadow: 0 2px 10px rgba(123,47,247,0.5);
        }}
        .hit-bar {{
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            height: 24px;
            overflow: hidden;
            margin-top: 15px;
        }}
        .hit-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00c853, #00e676);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 600;
            color: #000;
        }}
        .ece-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            margin-bottom: 8px;
        }}
        .ece-name {{ color: #888; }}
        .ece-val {{ font-weight: 700; font-size: 1.1rem; }}
        .ece-good {{ color: #00c853; }}
        .ece-warn {{ color: #ff9800; }}
        .ece-bad {{ color: #f44336; }}
        .delay-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 12px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            margin-bottom: 6px;
            font-size: 0.9rem;
        }}
        .delay-id {{ color: #00d4ff; }}
        .delay-info {{ color: #666; font-size: 0.8rem; }}
        .btn {{
            display: block;
            width: 100%;
            padding: 14px;
            background: linear-gradient(90deg, #7b2ff7, #00d4ff);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 20px;
        }}
        .btn:hover {{ opacity: 0.9; }}
        .wide {{ grid-column: span 2; }}
        @media (max-width: 768px) {{
            .wide {{ grid-column: span 1; }}
            .stat-row {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        .compare-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }}
        .compare-box {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }}
        .compare-label {{ font-size: 0.8rem; color: #888; margin-bottom: 10px; }}
        .compare-value {{ font-size: 1rem; font-weight: 600; }}
        .new-system {{ color: #00d4ff; }}
        .hermes-system {{ color: #7b2ff7; }}
        .common-box {{
            margin-top: 15px;
            padding: 12px;
            background: rgba(0,200,83,0.1);
            border-radius: 8px;
            text-align: center;
        }}
        .common-label {{ color: #888; font-size: 0.85rem; }}
        .common-value {{ color: #00c853; font-size: 1.2rem; font-weight: 700; margin-top: 5px; }}
        .update-time {{
            text-align: center;
            color: #555;
            font-size: 0.8rem;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Ralph Ecosystem</h1>
            <p class="subtitle">AI开发生态系统状态监控</p>
        </header>

        <div class="grid">
            <!-- 系统状态 -->
            <div class="card wide">
                <div class="card-title">⚙️ 系统状态</div>
                <div class="stat-row">
                    <div class="stat-box">
                        <div class="stat-value">11</div>
                        <div class="stat-label">Skills</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">58</div>
                        <div class="stat-label">Agents</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">14</div>
                        <div class="stat-label">Layers</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{len(tracker.pending_tasks)}</div>
                        <div class="stat-label">待处理检查点</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{len(tracker.tracked_tasks)}</div>
                        <div class="stat-label">追踪任务</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{sum(ece_data.values())/len(ece_data) if ece_data else 0.2:.2f}</div>
                        <div class="stat-label">Overall ECE</div>
                    </div>
                </div>
                <div class="hit-bar">
                    <div class="hit-fill" style="width: {lottery_data['hitRate']*100:.1f}%">
                        回测准确率: <span>{lottery_data['hitRate']*100:.1f}%</span>
                    </div>
                </div>
            </div>

            <!-- 六肖预测 -->
            <div class="card lottery-card">
                <div class="card-title">🎯 六肖预测</div>
                <div class="period">预测期号</div>
                <div class="period-num">{lottery_data['period']}</div>
                <div class="zodiac-list">
"""

    for z in lottery_data['top6']:
        html += f'<span class="zodiac-tag recommended">{z}</span>'

    all_zodiacs = ['龍', '鼠', '牛', '虎', '兔', '蛇', '馬', '羊', '猴', '雞', '狗', '豬']
    for z in all_zodiacs:
        if z not in lottery_data['top6']:
            html += f'<span class="zodiac-tag">{z}</span>'

    html += f"""
                </div>
                <div class="period" style="margin-top:15px;font-size:0.8rem">
                    回测准确率: <strong>{lottery_data['hitRate']*100:.1f}%</strong> (样本250期)
                </div>
                <button class="btn" onclick="window.location.reload()">🔄 刷新页面</button>
            </div>

            <!-- ECE校准 -->
            <div class="card">
                <div class="card-title">📊 ECE 校准详情</div>
"""

    for tt, ece in ece_data.items():
        cls = 'ece-good' if ece < 0.1 else 'ece-warn' if ece < 0.15 else 'ece-bad'
        html += f"""                <div class="ece-item">
                    <span class="ece-name">{tt}</span>
                    <span class="ece-val {cls}">{ece:.3f}</span>
                </div>
"""

    html += """            </div>

            <!-- 延迟跟踪 -->
            <div class="card">
                <div class="card-title">🔄 延迟跟踪器</div>
"""

    for d in delay_data:
        html += f"""                <div class="delay-item">
                    <span class="delay-id">{d['id']}</span>
                    <span class="delay-info">{d['checkpoints']}</span>
                </div>
"""

    html += f"""            </div>

            <!-- 预测对比 -->
            <div class="card">
                <div class="card-title">⚖️ 系统对比</div>
                <div class="compare-grid">
                    <div class="compare-box">
                        <div class="compare-label">生态新系统</div>
                        <div class="compare-value new-system">{' / '.join(lottery_data['top6']) if lottery_data['top6'] else '-'}</div>
                    </div>
                    <div class="compare-box">
                        <div class="compare-label">Hermes v7</div>
                        <div class="compare-value hermes-system">{' / '.join(hermes_data['top6']) if hermes_data['top6'] else '-'}</div>
                    </div>
                </div>
                <div class="common-box">
                    <div class="common-label">共同生肖</div>
                    <div class="common-value">{' / '.join(common) if common else '无'}</div>
                </div>
            </div>
        </div>

        <div class="update-time">
            最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""

    return html


if __name__ == '__main__':
    html = generate_dashboard()
    output_path = '/mnt/e/黑曜石/04_工作/AI开发生态系统/dashboard/index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Dashboard generated: {output_path}")