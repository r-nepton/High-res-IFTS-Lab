interface SummaryCardProps {
  label: string;
  value: string;
  detail?: string;
}

export function SummaryCard({ label, value, detail }: SummaryCardProps) {
  return (
    <div className="summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}
