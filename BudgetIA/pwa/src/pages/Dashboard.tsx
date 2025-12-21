import { useState, useEffect } from 'react';
import { fetchAPI } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowUpCircle, ArrowDownCircle, Wallet, Activity } from 'lucide-react';
import { cn } from '../utils/cn';

interface Summary {
  saldo_atual: number;
  total_receitas: number;
  total_despesas: number;
  [key: string]: number;
}

interface Transaction {
    Data: string;
    Descricao: string;
    Valor: number;
    Tipo: string;
    Categoria: string;
    Status: string;
}

interface Budget {
    Categoria: string;
    'Valor Limite': number;
    'Valor Gasto Atual': number;
}

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [expenses, setExpenses] = useState<{ name: string; value: number }[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
        try {
            const [summaryData, expensesData, txData] = await Promise.all([
                fetchAPI('/dashboard/summary'),
                fetchAPI('/dashboard/expenses_by_category?top_n=5'),
                fetchAPI('/transactions?limit=5')
            ]);

            setSummary(summaryData);
            
            // Transform expenses dict to array for Recharts
            if (expensesData) {
                const chartData = Object.entries(expensesData).map(([name, value]) => ({
                    name,
                    value: value as number
                }));
                setExpenses(chartData);
            }

            setTransactions(txData || []);
        } catch (error) {
            console.error("Failed to load dashboard data", error);
        } finally {
            setLoading(false);
        }
    }

    loadData();
  }, []);

  if (loading) {
      return <div className="text-white">Carregando dados financeiros...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Visão Geral</h2>
        <p className="text-gray-400">Acompanhe seu desempenho financeiro em tempo real.</p>
      </div>
      
      {/* KPI Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard 
            title="Saldo Calculado" 
            value={(summary?.total_receitas || 0) - (summary?.total_despesas || 0)} 
            icon={Wallet} 
            color="text-emerald-400"
        />
        <KpiCard 
            title="Receitas (Mês)" 
            value={summary?.total_receitas || 0} 
            icon={ArrowUpCircle} 
            color="text-blue-400"
        />
        <KpiCard 
            title="Despesas (Mês)" 
            value={summary?.total_despesas || 0} 
            icon={ArrowDownCircle} 
            color="text-red-400"
        />
        <KpiCard 
            title="Saldo (Fluxo)" 
            value={(summary?.total_receitas || 0) - (summary?.total_despesas || 0)} 
            icon={Activity} 
            color="text-emerald-400"
        />
      </div>

      {/* Budget Summary Section */}
      <BudgetSummaryWidget />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Chart Section */}
        <div className="col-span-4 rounded-xl border border-gray-800 bg-gray-900/50 p-6 text-white min-h-[400px]">
            <h3 className="mb-6 text-lg font-semibold">Despesas por Categoria (Top 5)</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={expenses} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                        <XAxis type="number" stroke="#9CA3AF" />
                        <YAxis dataKey="name" type="category" width={100} stroke="#9CA3AF" fontSize={12} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                            itemStyle={{ color: '#fff' }}
                            cursor={{fill: '#374151', opacity: 0.4}}
                        />
                        <Bar dataKey="value" fill="#34D399" radius={[0, 4, 4, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>

        {/* Recent Transactions */}
        <div className="col-span-3 rounded-xl border border-gray-800 bg-gray-900/50 p-6 text-white">
            <h3 className="mb-6 text-lg font-semibold">Últimas Transações</h3>
            <div className="space-y-4">
                {transactions.map((tx, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-800 transition-colors">
                        <div className="flex items-center space-x-4">
                            <div className={cn(
                                "h-10 w-10 rounded-full flex items-center justify-center",
                                tx.Tipo === "Receita" ? "bg-blue-500/20 text-blue-400" : "bg-red-500/20 text-red-400"
                            )}>
                                {tx.Tipo === "Receita" ? <ArrowUpCircle size={20} /> : <ArrowDownCircle size={20} />}
                            </div>
                            <div>
                                <p className="text-sm font-medium text-white">{tx.Descricao}</p>
                                <p className="text-xs text-gray-500">{tx.Categoria} • {new Date(tx.Data).toLocaleDateString()}</p>
                            </div>
                        </div>
                        <div className={cn(
                            "text-sm font-bold",
                            tx.Tipo === "Receita" ? "text-blue-400" : "text-white"
                        )}>
                            {tx.Tipo === "Despesa" ? "-" : "+"} {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(tx.Valor)}
                        </div>
                    </div>
                ))}
                {transactions.length === 0 && <p className="text-gray-500 text-sm">Nenhuma transação recente.</p>}
            </div>
        </div>
      </div>
    </div>
  );
}

function BudgetSummaryWidget() {
    const [budgets, setBudgets] = useState<Budget[]>([]);
    
    useEffect(() => {
        fetchAPI('/dashboard/budgets').then(data => {
            if (data) setBudgets(data);
        });
    }, []);

    if (budgets.length === 0) return null;

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
             {budgets.map((budget, idx) => {
                const limit = budget['Valor Limite'] || 0;
                const spent = budget['Valor Gasto Atual'] || 0;
                const progress = limit > 0 ? Math.min((spent / limit) * 100, 100) : 0;
                const isOver = spent > limit;

                return (
                    <div key={idx} className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
                        <div className="flex justify-between items-center mb-2">
                             <span className="font-semibold text-white truncate">{budget.Categoria}</span>
                             <span className={cn("text-xs font-bold px-2 py-0.5 rounded-full", isOver ? "bg-red-900 text-red-200" : "bg-emerald-900 text-emerald-200")}>
                                {new Intl.NumberFormat('pt-BR', { style: 'percent' }).format(Math.min(spent/limit, 1))}
                             </span>
                        </div>
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(spent)}</span>
                            <span>de {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(limit)}</span>
                        </div>
                         <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                            <div 
                                className={cn("h-full rounded-full transition-all duration-500", isOver ? "bg-red-500" : "bg-emerald-500")}
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>
                )
             })}
        </div>
    )
}

function KpiCard({ title, value, icon: Icon, color }: { title: string, value: number, icon: any, color: string }) {
    return (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 shadow-sm hover:border-emerald-500/50 transition-colors">
            <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="text-sm font-medium text-gray-400">{title}</div>
                <Icon className={cn("h-4 w-4", color)} />
            </div>
            <div className="text-2xl font-bold text-white">
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)}
            </div>
        </div>
    )
}
