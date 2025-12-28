import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/Tooltip";
import { cn } from "../../utils/cn";
import { useCategoryColorMap } from "../../hooks/useCategoryColorMap";

export function CategoryStackedBar({ data }: { data: { name: string; value: number }[] }) {
  const { getCategoryColor } = useCategoryColorMap();
  
  // Sort data descending to ensure Rank 0 (Highest) = Red
  const chartData = [...data].sort((a, b) => b.value - a.value);
  const total = chartData.reduce((acc, curr) => acc + curr.value, 0);

  if (total === 0) return (
      <div className="w-full text-center text-xs text-gray-500 py-2">Sem despesas registradas</div>
  );

  return (
    <div className="w-full space-y-3">
        {/* The Bar - Thinner (h-2) similar to budget bar */}
      <div className="h-2 w-full flex rounded-full overflow-hidden bg-gray-800">
        {chartData.map((item) => {
          if (item.value <= 0) return null;
          const percentage = (item.value / total) * 100;
          // Use Global Consistent Color
          const color = getCategoryColor(item.name);

          return (
            <TooltipProvider 
                key={item.name} 
                style={{ width: `${percentage}%` }}
                className="h-full"
            >
              <Tooltip>
                <TooltipTrigger className="h-full w-full">
                  <div
                    className={cn("h-full w-full transition-all hover:opacity-80 cursor-pointer border-r border-gray-900 last:border-0")}
                    style={{ backgroundColor: color }}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="font-semibold">{item.name}</p>
                  <p className="text-xs text-gray-400">
                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.value)}
                    {' '}({percentage.toFixed(1)}%)
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}
      </div>

      {/* The Legend - With Values */}
      <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[10px] md:text-xs text-gray-400">
        {chartData.map((item) => {
           if (item.value <= 0) return null;
           const color = getCategoryColor(item.name);
           return (
            <div key={item.name} className="flex items-center gap-1.5 min-w-0">
                <div 
                    className="w-2 h-2 rounded-full flex-shrink-0" 
                    style={{ backgroundColor: color }}
                />
                <div className="flex items-baseline gap-1 truncate">
                    <span className="truncate max-w-[80px] md:max-w-none font-medium">{item.name}</span>
                    <span className="text-white/60">
                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: "compact" }).format(item.value)}
                    </span>
                </div>
            </div>
           )
        })}
      </div>
    </div>
  );
}
