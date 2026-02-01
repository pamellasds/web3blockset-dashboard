import type { LucideIcon } from "lucide-react";
import { formatNumber } from "../../utils/formatNumber";

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  subtitle?: string;
  color?: string;
}

export default function StatCard({ label, value, icon: Icon, subtitle, color = "text-primary-600" }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-border p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-500 truncate">{label}</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">
            {typeof value === "number" ? formatNumber(value) : value}
          </p>
          {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
        </div>
        <div className={`p-2 rounded-lg bg-slate-50 ${color}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}
