import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

interface Series {
  key: string;
  label: string;
  color: string;
}

interface ChartPanelProps {
  title: string;
  data: Array<Record<string, number>>;
  series: Series[];
  yLabel?: string;
}

export function ChartPanel({ title, data, series, yLabel }: ChartPanelProps) {
  return (
    <section className="panel chart-panel">
      <div className="panel-header">
        <h3>{title}</h3>
        {yLabel ? <span>{yLabel}</span> : null}
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 10, right: 24, bottom: 10, left: 12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#233149" />
            <XAxis dataKey="wavelength_nm" tick={{ fill: "#9fb1c7", fontSize: 12 }} />
            <YAxis tick={{ fill: "#9fb1c7", fontSize: 12 }} />
            <Tooltip
              contentStyle={{ background: "#101827", border: "1px solid #2b3b57", color: "#e9f0fb" }}
              formatter={(value, name) => [Number(value ?? 0).toPrecision(4), String(name)]}
              labelFormatter={(value) => `${Number(value).toFixed(1)} nm`}
            />
            {series.map((item) => (
              <Line
                key={item.key}
                type="monotone"
                dataKey={item.key}
                name={item.label}
                stroke={item.color}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
