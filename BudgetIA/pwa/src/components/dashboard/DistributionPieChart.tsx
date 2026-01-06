import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { ExpenseData } from '../../types/domain';

interface Props {
  data: ExpenseData[];
  getCategoryColor: (category: string) => string;
}

export function DistributionPieChart({ data, getCategoryColor }: Props) {
  if (data.length === 0) {
    return (
      <div className="h-[250px] w-full bg-surface-card/40 rounded-xl border border-border flex items-center justify-center text-text-muted">
        Sem dados para exibir
      </div>
    );
  }

  return (
    <div className="h-[250px] md:h-[350px] w-full bg-surface-card/40 rounded-xl border border-border p-2 flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={3}
            cornerRadius={4}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={getCategoryColor(entry.name)} 
                stroke="rgba(0,0,0,0.1)" 
                strokeWidth={1} 
              />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'var(--color-surface)', 
              border: '1px solid var(--color-border)', 
              borderRadius: '8px', 
              color: 'var(--color-text-primary)' 
            }}
            itemStyle={{ color: 'var(--color-text-primary)' }}
            formatter={(value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
