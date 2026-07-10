import ReactECharts from 'echarts-for-react';

interface Props {
  categories: string[];
  series: { name: string; data: number[] }[];
  chartType?: 'line' | 'bar';
}

export default function ChartComponent({ categories, series, chartType = 'line' }: Props) {
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: series.map((s) => s.name) },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value' },
    series: series.map((s) => ({
      name: s.name,
      type: chartType,
      data: s.data,
      smooth: chartType === 'line',
    })),
  };
  return <ReactECharts option={option} style={{ height: 360 }} />;
}
