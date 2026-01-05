import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
    Brain, 
    ShieldCheck, 
    Sparkles, 
    ArrowRight,
    TrendingUp,
    Zap,
    FileSpreadsheet,
    DownloadCloud 
} from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { PLANS } from '../config/plans';

export default function Landing() {
    const navigate = useNavigate();

    const features = [
        {
            icon: <Brain className="w-6 h-6 text-emerald-400" />,
            title: "Inteligência Real",
            desc: "Não é apenas um dashboard. É um assistente que aprende seus hábitos e categoriza seus gastos automaticamente.",
            color: "emerald"
        },
        {
            icon: <ShieldCheck className="w-6 h-6 text-blue-400" />,
            title: "Proativo & Seguro",
            desc: "O sistema detecta anomalias e te avisa antes que você estoure o orçamento. Segurança total com seus dados.",
            color: "blue"
        },
        {
            icon: <Sparkles className="w-6 h-6 text-emerald-300" />,
            title: "Faxineiro Autônomo",
            desc: "Esqueça a organização manual. O BudgetIA limpa e organiza transações mal classificadas enquanto você dorme.",
            color: "emerald"
        }
    ];

    return (
        <div className="h-screen w-full overflow-y-auto overflow-x-hidden bg-gray-950 text-white selection:bg-emerald-500/30">
            {/* Background Gradients (Matches Login) */}
            <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
                 <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/40 via-gray-900 to-black opacity-90"></div>
                 <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
                 <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
            </div>

            {/* Navbar */}
            <nav className="relative z-10 flex items-center justify-between px-6 py-6 max-w-7xl mx-auto">
                {/* Logo from Login */}
                <div className="flex items-center gap-3">
                     <div className="relative h-10 w-10 overflow-hidden rounded-xl shadow-black/50 shadow-md ring-1 ring-white/10 shrink-0 group">
                         <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                         <img src="/pwa-512x512.png" alt="Icon" className="h-full w-full object-cover transform group-hover:scale-105 transition-transform duration-500" />
                    </div>
                    <div className="text-2xl font-bold tracking-tight leading-normal whitespace-nowrap drop-shadow-sm flex items-center">
                        <span className="text-transparent bg-clip-text bg-gradient-to-br from-white to-gray-400">Budget</span>
                        <span className="text-emerald-400 drop-shadow-glow">IA</span>
                    </div>
                </div>
                
                <Button 
                    variant="outline"
                    onClick={() => navigate('/')}
                    className="rounded-full border-white/10 hover:bg-white/5 backdrop-blur-md"
                >
                    Entrar
                </Button>
            </nav>

            {/* Hero Section */}
            <main className="relative z-10 px-6 pt-20 pb-32 max-w-7xl mx-auto text-center">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                >
                    
                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 text-white">
                        Domine suas finanças com<br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">
                            Inteligência Artificial
                        </span>
                    </h1>
                    
                    <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                        Abandone as planilhas manuais. O BudgetIA é o seu "Jarvis" pessoal para finanças: 
                        proativo, inteligente e totalmente integrado ao seu dia a dia.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Button 
                            size="lg"
                            className="rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-[0_0_20px_-5px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_-5px_rgba(16,185,129,0.5)] transition-all flex items-center gap-2"
                            onClick={() => navigate('/')}
                        >
                            Começar Agora
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </Button>
                        <Button 
                            variant="ghost"
                            size="lg"
                            className="rounded-full text-white hover:bg-white/5 border border-white/5 backdrop-blur-sm"
                            onClick={() => window.open('https://github.com/lucianobtorres', '_blank')}
                        >
                            Ver no GitHub
                        </Button>
                    </div>
                </motion.div>

                {/* Multi-Layer 3D Composition */}
                <div className="mt-20 relative mx-auto max-w-7xl h-[600px] perspective-2000 pointer-events-none md:pointer-events-auto">
                    {/* Atmospheric Glows */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/10 blur-[120px] rounded-full mix-blend-screen" />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-blue-500/10 blur-[100px] rounded-full mix-blend-screen" />

                    <motion.div
                        className="relative w-full h-full transform-style-3d"
                        initial={{ rotateX: 20, rotateY: 0, scale: 0.9 }}
                        animate={{ 
                            rotateX: 15,
                            rotateY: [0, -5, 0, 5, 0],
                        }}
                        transition={{
                            rotateY: { duration: 10, repeat: Infinity, ease: "easeInOut" }
                        }}
                        style={{ transformStyle: 'preserve-3d' }}
                    >
                        {/* LAYER 1: Main Dashboard (Base) */}
                        <div 
                            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-[40%] w-[900px] h-[550px] bg-[#0A0A0B] rounded-xl border border-white/10 shadow-2xl flex overflow-hidden"
                            style={{ transform: 'translateZ(0px)' }}
                        >
                            {/* Sidebar Mock */}
                            <div className="w-64 bg-[#0F0F11] border-r border-white/5 p-4 flex flex-col gap-4">
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20" />
                                    <div className="h-4 w-24 bg-white/10 rounded" />
                                </div>
                                {[1,2,3,4,5].map(i => (
                                    <div key={i} className="h-10 w-full rounded-lg bg-white/5 flex items-center px-3 gap-3">
                                        <div className={`w-4 h-4 rounded-full ${i===1 ? 'bg-emerald-500/50' : 'bg-white/10'}`} />
                                        <div className="h-2 w-20 bg-white/10 rounded" />
                                    </div>
                                ))}
                            </div>
                            {/* Main Content Mock */}
                            <div className="flex-1 p-8 bg-[#0A0A0B]">
                                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                                    Visão Geral
                                    <div className="px-2 py-0.5 rounded text-[10px] bg-white/5 border border-white/5 text-gray-500">PRO</div>
                                </h3>
                                {/* KPI Row */}
                                <div className="grid grid-cols-3 gap-4 mb-8">
                                    <div className="p-4 rounded-xl bg-[#121214] border border-white/5">
                                        <div className="text-xs text-gray-400 mb-1">SALDO ATUAL</div>
                                        <div className="text-2xl font-bold text-emerald-400">R$ 12.450</div>
                                    </div>
                                    <div className="p-4 rounded-xl bg-[#121214] border border-white/5">
                                        <div className="text-xs text-gray-400 mb-1">RECEITAS</div>
                                        <div className="text-2xl font-bold text-blue-400">R$ 22.000</div>
                                    </div>
                                    <div className="p-4 rounded-xl bg-[#121214] border border-white/5">
                                        <div className="text-xs text-gray-400 mb-1">DESPESAS</div>
                                        <div className="text-2xl font-bold text-red-400">R$ 9.550</div>
                                    </div>
                                </div>
                                {/* Budgets List */}
                                <div className="p-4 rounded-xl bg-[#121214] border border-white/5">
                                    <div className="flex justify-between mb-4">
                                        <div className="h-4 w-32 bg-white/10 rounded" />
                                        <div className="h-4 w-4 bg-white/10 rounded" />
                                    </div>
                                    {[1,2,3].map(i => (
                                        <div key={i} className="mb-4 last:mb-0">
                                            <div className="flex justify-between text-xs text-gray-400 mb-1">
                                                <span>Categoria {i}</span>
                                                <span>{75 - (i*10)}%</span>
                                            </div>
                                            <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                                <div className="h-full bg-emerald-500/50 rounded-full" style={{ width: `${75 - (i*10)}%`}} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* LAYER 2: Intelligence Panel (Floating Left) */}
                        <motion.div 
                            className="absolute top-[20%] -left-[5%] w-[320px] bg-[#0F0F11] rounded-xl border border-emerald-500/30 shadow-2xl overflow-hidden"
                            style={{ transform: 'translateZ(100px)' }}
                            animate={{ y: [0, -10, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                        >
                            <div className="p-4 border-b border-white/5 bg-emerald-900/10 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Brain className="w-4 h-4 text-emerald-400" />
                                    <span className="text-sm font-bold text-emerald-100">Cérebro da IA</span>
                                </div>
                                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                            </div>
                            <div className="p-4 space-y-3">
                                {/* Tool Item */}
                                <div className="p-3 rounded-lg bg-pink-500/10 border border-pink-500/20">
                                    <div className="text-xs font-bold text-pink-400 mb-1">FAXINEIRO AUTÔNOMO</div>
                                    <div className="text-xs text-gray-400">23 transações corrigidas automaticamente nesta madrugada.</div>
                                </div>
                                {/* Observer Item */}
                                <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                    <div className="text-xs font-bold text-blue-400 mb-1">OBSERVADOR ATIVO</div>
                                    <div className="text-xs text-gray-400">Monitorando gastos com "Alimentação" vs Orçamento.</div>
                                </div>
                            </div>
                        </motion.div>

                        {/* LAYER 3: Chart Panel (Floating Right) */}
                        <motion.div 
                            className="absolute top-[30%] -right-[5%] w-[340px] bg-[#0F0F11] rounded-xl border border-white/10 shadow-2xl overflow-hidden"
                            style={{ transform: 'translateZ(80px)' }}
                            animate={{ y: [0, -15, 0] }}
                            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                        >
                            <div className="p-4 border-b border-white/5 flex justify-between items-center">
                                <span className="text-sm font-bold text-white">Gastos por Categoria</span>
                            </div>
                            <div className="p-6 flex items-center justify-center relative">
                                {/* Donut Chart Simulation */}
                                <div className="w-32 h-32 rounded-full border-[12px] border-emerald-500/20 border-t-emerald-500 border-r-blue-500 border-l-pink-500 rotate-45 relative">
                                    <div className="absolute inset-0 flex items-center justify-center flex-col">
                                        <span className="text-xs text-gray-500">Total</span>
                                        <span className="text-sm font-bold text-white">R$ 9.5k</span>
                                    </div>
                                </div>
                            </div>
                             <div className="px-4 pb-4 space-y-2">
                                <div className="flex items-center justify-between text-xs">
                                    <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-pink-500" /> Alimentação</span>
                                    <span className="text-white">R$ 1.200</span>
                                </div>
                                <div className="flex items-center justify-between text-xs">
                                    <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500" /> Moradia</span>
                                    <span className="text-white">R$ 3.500</span>
                                </div>
                            </div>
                        </motion.div>

                        {/* LAYER 4: Notification (Floating Center Front) */}
                        <motion.div 
                            className="absolute bottom-[-5%] left-[60%] w-[280px] bg-[#1a1a1e] rounded-lg border border-emerald-500/50 shadow-2xl shadow-emerald-500/20 p-4"
                            style={{ transform: 'translateZ(150px)' }}
                            initial={{ opacity: 0, y: 50 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 1.5, duration: 0.8 }}
                        >
                            <div className="flex gap-3">
                                <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
                                    <Sparkles className="w-5 h-5 text-emerald-400" />
                                </div>
                                <div>
                                    <div className="text-sm font-bold text-white">Dica Proativa</div>
                                    <div className="text-xs text-gray-400 mt-1">
                                        Percebi que sua conta de Luz veio 15% mais alta. Gostaria de analisar?
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                </div>

                {/* DEEP DIVE SECTIONS */}

                {/* THE HOOK: The Problem */}
                <div className="mt-32 mb-32 text-center max-w-3xl mx-auto space-y-6">
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
                        O fim do "Dia de Preencher Planilha"
                    </h2>
                    <p className="text-lg text-gray-400 leading-relaxed">
                        Apps de banco mostram o passado. Planilhas manuais dão trabalho demais. 
                        Apps tradicionais prendem seus dados. <br/>
                        <span className="text-emerald-400 font-medium">O BudgetIA é diferente.</span>
                    </p>
                    <div className="pt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
                        <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                            <div className="text-red-400 mb-2 text-sm font-bold">🚫 Apps Tradicionais</div>
                            <div className="text-sm text-gray-500">Dados presos, gráficos limitados e zero personalização.</div>
                        </div>
                        <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                            <div className="text-yellow-400 mb-2 text-sm font-bold">⚠️ Planilhas Manuais</div>
                            <div className="text-sm text-gray-500">Poderosas, mas exigem horas de digitação e manutenção.</div>
                        </div>
                        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 relative overflow-hidden">
                            <div className="absolute inset-0 bg-emerald-500/10 blur-xl"></div>
                            <div className="relative z-10">
                                <div className="text-emerald-400 mb-2 text-sm font-bold">✅ BudgetIA</div>
                                <div className="text-sm text-emerald-100/70">A liberdade do Excel com a automação da IA Generativa.</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* FEATURE: EXCEL SOVEREIGNTY */}
                <div className="mt-32 flex flex-col items-center text-center gap-8">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium">
                        <FileSpreadsheet className="w-3 h-3" />
                        <span>Soberania de Dados</span>
                    </div>
                     <h2 className="text-3xl md:text-5xl font-bold max-w-4xl">
                        Seus dados, Suas regras.<br/>
                        <span className="text-green-400">Poder total ao Excel.</span>
                    </h2>
                    <p className="text-gray-400 text-lg max-w-2xl">
                        Diferente de outros apps, não guardamos sua vida num banco de dados obscuro. 
                        Tudo é salvo em uma <b>Planilha Mestra (.xlsx)</b> que você pode abrir, auditar e copiar a qualquer momento.
                    </p>
                    
                    {/* Visual Connection */}
                    <div className="relative w-full max-w-4xl h-40 md:h-64 mt-8 flex items-center justify-center">
                        {/* Connecting Line */}
                        <div className="absolute top-1/2 left-1/4 right-1/4 h-[2px] bg-gradient-to-r from-green-500/50 via-emerald-500 to-purple-500/50 dashed-line" />
                        
                        {/* Excel Node */}
                        <motion.div 
                            whileHover={{ scale: 1.1 }}
                            className="absolute left-[10%] md:left-[20%] w-24 h-24 md:w-32 md:h-32 bg-[#1d6f42] rounded-2xl flex items-center justify-center shadow-[0_0_30px_rgba(29,111,66,0.4)] border border-white/20 z-10"
                        >
                            <FileSpreadsheet className="w-12 h-12 md:w-16 md:h-16 text-white" />
                            <div className="absolute -bottom-8 text-sm font-mono text-green-400 opacity-80">planilha.xlsx</div>
                        </motion.div>

                        {/* Arrows Animation */}
                        <div className="absolute flex gap-2">
                             <motion.div 
                                animate={{ x: [0, 100, 0], opacity: [0, 1, 0] }}
                                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                                className="w-2 h-2 rounded-full bg-white shadow-[0_0_10px_white]"
                             />
                             <motion.div 
                                animate={{ x: [0, -100, 0], opacity: [0, 1, 0] }}
                                transition={{ duration: 3, repeat: Infinity, ease: "linear", delay: 1.5 }}
                                className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_emerald-400]"
                             />
                        </div>

                        {/* Brain Node */}
                        <motion.div 
                            whileHover={{ scale: 1.1 }}
                            className="absolute right-[10%] md:right-[20%] w-24 h-24 md:w-32 md:h-32 bg-indigo-600/20 backdrop-blur-md rounded-2xl flex items-center justify-center shadow-[0_0_30px_rgba(79,70,229,0.2)] border border-indigo-500/30 z-10"
                        >
                            <Brain className="w-12 h-12 md:w-16 md:h-16 text-indigo-400" />
                            <div className="absolute -bottom-8 text-sm font-mono text-indigo-400 opacity-80">Agente IA</div>
                        </motion.div>
                    </div>
                </div>
                
                {/* Section 1: The Cleaner (Existing) */}
                <div className="mt-40 flex flex-col md:flex-row items-center gap-12">
                     <div className="flex-1 text-left space-y-6">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/20 text-pink-400 text-sm font-medium">
                            <Sparkles className="w-3 h-3" />
                            <span>Novo: Faxineiro Autônomo</span>
                        </div>
                        <h2 className="text-3xl md:text-4xl font-bold">
                            Enquanto você dorme,<br/>
                            <span className="text-pink-400">nós organizamos tudo.</span>
                        </h2>
                        <p className="text-gray-400 text-lg leading-relaxed">
                            Cansado de categorizar "Pix enviado" ou "Uber"? 
                            Nosso agente de limpeza roda toda madrugada, analisa suas transações sem categoria e, 
                            usando LLMs avançados, atribui a categoria correta com precisão humana.
                        </p>
                        <div className="flex flex-col gap-3">
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/5">
                                <div className="line-through text-gray-500 text-sm">UBER *VIAGEM</div>
                                <ArrowRight className="w-4 h-4 text-gray-500" />
                                <div className="text-emerald-400 font-bold text-sm">Transporte</div>
                            </div>
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/5">
                                <div className="line-through text-gray-500 text-sm">IFD *LANCHES</div>
                                <ArrowRight className="w-4 h-4 text-gray-500" />
                                <div className="text-pink-400 font-bold text-sm">Alimentação</div>
                            </div>
                        </div>
                     </div>
                     <div className="flex-1 w-full relative h-[400px]">
                        <div className="absolute inset-0 bg-gradient-to-tr from-pink-500/20 to-transparent blur-3xl opacity-30" />
                        <div className="relative z-10 w-full h-full bg-[#121214] rounded-2xl border border-white/10 p-6 flex flex-col gap-4 shadow-2xl rotate-3 hover:rotate-0 transition-transform duration-500">
                             {/* Mock Terminal/Log */}
                             <div className="flex items-center gap-2 mb-2">
                                <div className="w-3 h-3 rounded-full bg-red-500" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                                <div className="w-3 h-3 rounded-full bg-green-500" />
                                <div className="ml-auto text-xs text-gray-500 font-mono">sanitizer_job.py</div>
                             </div>
                             <div className="font-mono text-xs space-y-2 text-gray-300 overflow-hidden">
                                <div className="text-gray-500"># Iniciando rotina de limpeza...</div>
                                <div><span className="text-blue-400">INFO</span>: Encontradas 12 transações não categorizadas.</div>
                                <div><span className="text-purple-400">LLM</span>: Analisando "PAGTO ELECTRIC"...</div>
                                <div><span className="text-emerald-400">SUCCESS</span>: Classificado como [Moradia] (98% conf).</div>
                                <div><span className="text-purple-400">LLM</span>: Analisando "NETFLIX.COM"...</div>
                                <div><span className="text-emerald-400">SUCCESS</span>: Classificado como [Lazer/Streaming] (99% conf).</div>
                                <div className="text-gray-500">...</div>
                                <div className="text-emerald-400 mt-4">&gt;&gt; Limpeza concluída. Planilha atualizada.</div>
                             </div>
                        </div>
                     </div>
                </div>

                {/* Section 2: Integrations */}
                <div className="mt-40 mb-32 flex flex-col-reverse md:flex-row items-center gap-12">
                     <div className="flex-1 w-full relative h-[400px]">
                        <div className="absolute inset-0 bg-gradient-to-bl from-green-500/20 to-transparent blur-3xl opacity-30" />
                        <div className="relative z-10 w-full h-full grid grid-cols-2 gap-4">
                            {/* Chat Mock */}
                            <div className="col-span-2 md:col-span-1 bg-[#121214] rounded-2xl border border-white/10 p-4 flex flex-col justify-end gap-3 shadow-xl -rotate-3 hover:rotate-0 transition-transform duration-500">
                                <div className="self-end bg-emerald-600 text-white p-3 rounded-2xl rounded-tr-none text-sm max-w-[90%]">
                                    Gastei 45 reais na padaria agora
                                </div>
                                <div className="self-start bg-[#1A1A1E] text-gray-200 p-3 rounded-2xl rounded-tl-none text-sm max-w-[90%] border border-white/5">
                                    <div className="text-emerald-400 font-bold text-xs mb-1">BudgetIA</div>
                                    Anotado! Classifiquei como <b>Alimentação</b>. 🥐
                                    <br/>Seu saldo restante para alimentação é R$ 320.
                                </div>
                            </div>
                             {/* Telegram/WhatsApp Icons */}
                             <div className="col-span-2 md:col-span-1 flex flex-col gap-4 justify-center pl-8">
                                <div className="flex items-center gap-4 text-white/50 hover:text-white transition-colors">
                                    <div className="w-12 h-12 rounded-full bg-[#25D366]/20 flex items-center justify-center">
                                        <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-[#25D366]"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
                                    </div>
                                    <div className="font-medium">WhatsApp</div>
                                </div>
                                <div className="flex items-center gap-4 text-white/50 hover:text-white transition-colors">
                                    <div className="w-12 h-12 rounded-full bg-[#0088cc]/20 flex items-center justify-center">
                                         <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-[#0088cc]"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.06-.14-.04-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.62-.2-1.12-.31-1.08-.63.02-.16.24-.32.65-.48 2.53-1.1 4.23-1.83 5.11-2.19 2.51-1.02 3.03-1.19 3.37-1.19.07 0 .25.02.35.09.09.06.12.15.15.22.03.07.03.22.02.32z"/></svg>
                                    </div>
                                    <div className="font-medium">Telegram</div>
                                </div>
                             </div>
                        </div>
                     </div>
                     <div className="flex-1 text-left space-y-6">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium">
                            <Zap className="w-3 h-3" />
                            <span>Integração Total</span>
                        </div>
                        <h2 className="text-3xl md:text-4xl font-bold">
                            Fale com suas finanças<br/>
                            <span className="text-emerald-400">onde você estiver.</span>
                        </h2>
                        <p className="text-gray-400 text-lg leading-relaxed">
                            Não instale mais um app. O BudgetIA vive dentro do seu <b>WhatsApp</b> ou <b>Telegram</b>. 
                            Envie áudios, fotos de recibos ou apenas texto. 
                            A gente registra, categoriza e avisa sobre seu progresso.
                        </p>
                     </div>
                </div>

                {/* FEATURE: MOBILE EXPERIENCE */}
                <div className="mt-32 mb-32 flex flex-col md:flex-row items-center gap-16">
                    <div className="flex-1 space-y-6 text-left">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium">
                            <DownloadCloud className="w-3 h-3" />
                            <span>PWA Instalável</span>
                        </div>
                        <h2 className="text-3xl md:text-5xl font-bold">
                            Leve no seu bolso.<br/>
                            <span className="text-purple-400">Rápido como um raio.</span>
                        </h2>
                        <ul className="space-y-4 text-gray-400">
                            <li className="flex items-center gap-3">
                                <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400">⚡</div>
                                <span>Zero latência: interface otimizada para toque.</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400">📱</div>
                                <span>Instale sem App Store (Android e iOS).</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400">🔋</div>
                                <span>Baixíssimo consumo de bateria.</span>
                            </li>
                        </ul>
                        <Button 
                            variant="primary" 
                            className="mt-4 bg-purple-600 hover:bg-purple-500 rounded-full"
                            onClick={() => window.open('https://github.com/lucianobtorres/BudgetIA', '_blank')}
                        >
                            Ver Código Fonte
                        </Button>
                    </div>

                    {/* PHONE MOCKUP */}
                    <div className="relative">
                        <div className="absolute inset-0 bg-purple-500/20 blur-3xl -z-10" />
                        {/* Phone Frame */}
                        <div className="w-[300px] h-[600px] bg-[#0A0A0B] rounded-[40px] border-[8px] border-[#1A1A1E] shadow-2xl relative overflow-hidden ring-1 ring-white/10">
                            {/* Notch */}
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-6 bg-[#1A1A1E] rounded-b-2xl z-20" />
                            
                            {/* Screen Content */}
                            <div className="w-full h-full pt-8 px-4 flex flex-col gap-4">
                                {/* Mobile Header */}
                                <div className="flex justify-between items-center">
                                    <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-xs">U</div>
                                    <div className="font-bold text-white">BudgetIA</div>
                                    <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center pb-2">...</div>
                                </div>
                                
                                {/* Mobile Card */}
                                <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-900/50 to-emerald-900/10 border border-emerald-500/20">
                                    <div className="text-xs text-gray-400">Saldo Disponível</div>
                                    <div className="text-2xl font-bold text-white mt-1">R$ 12.450</div>
                                    <div className="mt-4 flex gap-2">
                                        <div className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold">+ Receita</div>
                                        <div className="px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-xs font-bold">- Despesa</div>
                                    </div>
                                </div>

                                {/* Mobile List */}
                                <div className="space-y-3">
                                    <h3 className="text-xs font-bold text-gray-500 uppercase">Hoje</h3>
                                    {[1,2,3,4].map(i => (
                                        <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                                            <div className="w-10 h-10 rounded-full bg-white/5" />
                                            <div className="flex-1">
                                                <div className="h-3 w-24 bg-white/10 rounded mb-1" />
                                                <div className="h-2 w-16 bg-white/5 rounded" />
                                            </div>
                                            <div className="h-4 w-12 bg-white/10 rounded" />
                                        </div>
                                    ))}
                                </div>

                                 {/* Mobile Floating Action Button */}
                                 <div className="absolute bottom-6 right-6 w-14 h-14 bg-emerald-500 rounded-full shadow-lg shadow-emerald-500/40 flex items-center justify-center text-white text-2xl font-bold">
                                    +
                                 </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* PRICING SECTION */}
                <div className="mt-40 mb-32 text-center max-w-5xl mx-auto">
                     <h2 className="text-3xl md:text-5xl font-bold mb-6">
                        Investimento Simples. <br/>
                        <span className="text-emerald-400">Retorno Imediato.</span>
                    </h2>
                    <p className="text-gray-400 mb-12 max-w-2xl mx-auto">
                        Quanto vale ter um analista financeiro pessoal disponível 24/7?
                        No BudgetIA, custa menos que um café.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start relative px-4">
                        {PLANS.map((plan) => (
                             <div key={plan.id} className="relative h-full">
                                {plan.variant === 'highlight' && (
                                     <div className="absolute -inset-[2px] bg-gradient-to-b from-emerald-500 to-blue-600 rounded-3xl blur-sm opacity-70 group-hover:opacity-100 transition-opacity" />
                                )}
                                
                                <div className={`relative p-8 rounded-3xl h-full flex flex-col ${
                                    plan.variant === 'highlight' ? 'bg-[#0A0A0B]' : 'bg-white/5 border border-white/10 hover:border-white/20 transition-colors'
                                }`}>
                                    {plan.variant === 'highlight' && (
                                        <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-emerald-500 to-blue-600 text-[10px] font-bold tracking-wider text-white uppercase shadow-lg">
                                            Mais Popular
                                        </div>
                                    )}

                                    <div className="text-left space-y-4 flex-1">
                                        {plan.variant === 'highlight' ? (
                                             <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-blue-400">
                                                {plan.name}
                                            </h3>
                                        ) : (
                                            <h3 className="text-xl font-bold text-gray-300">{plan.name}</h3>
                                        )}
                                       
                                        <div className="space-y-1">
                                            <div className="flex items-baseline gap-1">
                                                <span className="text-4xl font-bold text-white">{plan.price}</span>
                                                {plan.period && <span className="text-gray-500">{plan.period}</span>}
                                            </div>
                                            <p className="text-sm text-gray-500">{plan.description}</p>
                                        </div>

                                        <Button 
                                            className={`w-full ${
                                                plan.variant === 'highlight' 
                                                ? 'bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-500 hover:to-blue-500 text-white shadow-lg shadow-emerald-500/25' 
                                                : 'bg-white/10 hover:bg-white/20 text-white border border-white/5'
                                            }`}
                                            onClick={() => navigate('/')}
                                        >
                                            {plan.buttonText || 'Escolher Plano'}
                                        </Button>

                                        <ul className={`space-y-3 pt-6 text-sm text-left ${plan.variant === 'highlight' ? 'text-gray-300 font-medium' : 'text-gray-400'}`}>
                                            {plan.features.map((feature, idx) => (
                                                <li key={idx} className={`flex items-center gap-2 ${!feature.included ? 'opacity-50' : ''}`}>
                                                    {feature.included ? (
                                                        plan.variant === 'highlight' 
                                                        ? <Sparkles className="w-4 h-4 text-emerald-400" /> 
                                                        : <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                                    ) : (
                                                        <div className="w-1.5 h-1.5 rounded-full bg-gray-700" />
                                                    )}
                                                    <span>{feature.name}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                             </div>
                        ))}
                    </div>
                </div>

                {/* TRUST / OPEN SOURCE */}
                <div className="mt-20 py-12 border-t border-white/5 text-center">
                    <div className="max-w-4xl mx-auto px-6">
                         <div className="flex justify-center mb-6">
                            <ShieldCheck className="w-12 h-12 text-gray-600" />
                        </div>
                        <h3 className="text-2xl font-bold text-gray-300">Privacidade em Primeiro Lugar</h3>
                        <p className="text-gray-500 mt-4 max-w-2xl mx-auto">
                            O BudgetIA é um projeto <b>Open Source</b>. Isso significa que nosso código é aberto para auditoria de qualquer pessoa. 
                            Nós não vendemos seus dados. Nós não rastreamos você.
                        </p>
                        <div className="mt-8 flex justify-center gap-4">
                            <a href="https://github.com/lucianobtorres/BudgetIA" target="_blank" className="text-gray-400 hover:text-white underline text-sm transition-colors">Ver repositório no GitHub</a>
                            <span className="text-gray-600">•</span>
                            <a href="#" className="text-gray-400 hover:text-white underline text-sm transition-colors">Termos de Uso</a>
                        </div>
                    </div>
                </div>

                <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                    {features.map((feature, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: idx * 0.1 }}
                        >
                            <GlassCard className="h-full p-6 hover:bg-emerald-500/5 transition-colors group border-white/5">
                                <div className={`w-12 h-12 rounded-lg bg-${feature.color}-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                                    {feature.icon}
                                </div>
                                <h3 className="text-xl font-semibold mb-2 text-white">{feature.title}</h3>
                                <p className="text-gray-400 leading-relaxed text-sm">
                                    {feature.desc}
                                </p>
                            </GlassCard>
                        </motion.div>
                    ))}
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-white/5 bg-black/40 backdrop-blur-md">
                <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="text-gray-500 text-sm">
                        © 2026 BudgetIA. Construído com Paixão e IA.
                    </div>
                </div>
            </footer>
        </div>
    );
}
