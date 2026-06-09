"""
Data Visualizer - 数据可视化生成器
基于 AI 自动生成图表和可视化
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import json


@dataclass
class ChartConfig:
    type: str  # bar, line, pie, scatter, area
    title: str
    data: List[Dict]
    x_key: str
    y_key: str
    color: Optional[str] = None


class DataVisualizer:
    """数据可视化生成器"""

    def __init__(self):
        self.chart_library = "chart.js"  # 默认 Chart.js
        self.theme = "default"

    def generate_chart(self, data: List[Dict], chart_type: str = "auto", title: str = "图表") -> Dict[str, Any]:
        """
        根据数据生成图表配置

        Args:
            data: 数据列表
            chart_type: 图表类型 (bar, line, pie, scatter, area)
            title: 图表标题

        Returns:
            图表配置对象
        """
        if not data:
            return {"error": "数据不能为空"}

        # 自动推断图表类型
        if chart_type == "auto":
            chart_type = self._infer_chart_type(data)

        # 推断字段
        keys = list(data[0].keys())
        x_key = keys[0] if len(keys) > 0 else "x"
        y_key = keys[1] if len(keys) > 1 else "y"

        config = ChartConfig(
            type=chart_type,
            title=title,
            data=data,
            x_key=x_key,
            y_key=y_key
        )

        return self._build_chart_config(config)

    def _infer_chart_type(self, data: List[Dict]) -> str:
        """自动推断图表类型"""
        if len(data) > 20:
            return "line"  # 时间序列用线图
        elif all('percentage' in str(d).lower() or 'ratio' in str(d).lower() for d in data):
            return "pie"  # 比例用饼图
        return "bar"  # 默认用柱状图

    def _build_chart_config(self, config: ChartConfig) -> Dict[str, Any]:
        """构建 Chart.js 配置"""
        return {
            "type": config.type,
            "data": {
                "labels": [str(d.get(config.x_key, "")) for d in config.data],
                "datasets": [{
                    "label": config.title,
                    "data": [d.get(config.y_key, 0) for d in config.data],
                    "backgroundColor": self._get_colors(len(config.data)),
                    "borderColor": self._get_border_color(config.type),
                    "fill": config.type == "area",
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": bool(config.title),
                        "text": config.title
                    },
                    "legend": {
                        "display": config.type == "pie"
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        }

    def _get_colors(self, count: int) -> List[str]:
        """获取颜色数组"""
        base_colors = [
            "#3b82f6", "#ef4444", "#22c55e", "#f59e0b",
            "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"
        ]
        return base_colors[:count] if count <= len(base_colors) else base_colors * (count // len(base_colors) + 1)

    def _get_border_color(self, chart_type: str) -> str:
        """获取边框颜色"""
        border_colors = {
            "line": "#3b82f6",
            "area": "#22c55e",
        }
        return border_colors.get(chart_type, "")

    def generate_dashboard(self, charts: List[ChartConfig], layout: str = "grid") -> Dict[str, Any]:
        """生成仪表板配置"""
        return {
            "layout": layout,
            "charts": [
                self._build_chart_config(c) for c in charts
            ],
            "theme": self.theme
        }

    def export_html(self, chart_config: Dict[str, Any]) -> str:
        """导出为独立 HTML"""
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>{chart_config.get('data', {}).get('datasets', [{}])[0].get('label', 'Chart')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <canvas id="myChart"></canvas>
    <script>
        const config = {json.dumps(chart_config)};
        new Chart(document.getElementById('myChart'), config);
    </script>
</body>
</html>'''


if __name__ == "__main__":
    visualizer = DataVisualizer()

    # 示例数据
    data = [
        {"month": "1月", "sales": 120},
        {"month": "2月", "sales": 150},
        {"month": "3月", "sales": 180},
        {"month": "4月", "sales": 140},
    ]

    chart = visualizer.generate_chart(data, title="月度销售额")
    print(f"图表类型: {chart['type']}")
    print(f"数据点数: {len(chart['data']['datasets'][0]['data'])}")
