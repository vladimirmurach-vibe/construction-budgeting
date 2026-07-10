import ReactECharts from 'echarts-for-react';

type SeriesPoint = { period: string; revenue: number; costs: number; profit: number };

export function ConsolidationChart({ data }: { data: SeriesPoint[] }) {
  const option = {
    color: ['#0f766e', '#b45309', '#10161f'],
    tooltip: { trigger: 'axis' },
    legend: { data: ['Выручка', 'Затраты', 'Прибыль'], bottom: 0 },
    grid: { left: 48, right: 24, top: 24, bottom: 48 },
    xAxis: { type: 'category', data: data.map((d) => d.period) },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#e8edf2' } } },
    series: [
      { name: 'Выручка', type: 'line', smooth: true, data: data.map((d) => d.revenue) },
      { name: 'Затраты', type: 'line', smooth: true, data: data.map((d) => d.costs) },
      { name: 'Прибыль', type: 'bar', data: data.map((d) => d.profit), barMaxWidth: 28 },
    ],
  };
  return <ReactECharts option={option} style={{ height: 340 }} />;
}

export function CompareChart({
  rows,
}: {
  rows: { period: string; variance: number }[];
}) {
  const option = {
    color: ['#0f766e'],
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 24, bottom: 40 },
    xAxis: { type: 'category', data: rows.map((r) => r.period) },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#e8edf2' } } },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => r.variance),
        barMaxWidth: 36,
        itemStyle: {
          color: (p: { value: number }) => (p.value >= 0 ? '#0f766e' : '#b91c1c'),
        },
      },
    ],
  };
  return <ReactECharts option={option} style={{ height: 300 }} />;
}
