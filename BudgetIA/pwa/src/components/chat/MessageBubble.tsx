import { cn } from '../../utils/cn';
import ReactMarkdown from 'react-markdown';

export interface MessageProps {
    role: 'user' | 'assistant';
    content: string;
    steps?: {
        tool: string;
        tool_input: any;
        log: string;
        observation: string;
    }[];
}

interface MessageBubbleProps {
    message: MessageProps;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    return (
        <div className={cn("flex flex-col", message.role === 'user' ? "items-end" : "items-start")}>
            {/* Agent Thoughts (Intermediate Steps) */}
            {message.steps && message.steps.length > 0 && (
                <div className="mb-2 max-w-[90%]">
                    <details className="group">
                        <summary className="cursor-pointer text-xs text-emerald-400/70 hover:text-emerald-400 transition-colors flex items-center select-none list-none">
                            <div className="flex items-center space-x-2 bg-emerald-900/10 px-2.5 py-1 rounded-full border border-emerald-500/10 hover:border-emerald-500/30">
                                <span className="relative flex h-1.5 w-1.5">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                                </span>
                                <span className="text-[11px] font-medium">Processamento ({message.steps.length})</span>
                            </div>
                        </summary>
                        <div className="mt-2 space-y-2 pl-2 border-l-2 border-emerald-500/10 ml-4">
                            {message.steps.map((step, sIdx) => (
                                <div key={sIdx} className="text-xs bg-gray-900/50 p-2 rounded border border-gray-800">
                                    <div className="font-semibold text-emerald-300 mb-1 flex items-center justify-between">
                                        <span>🛠️ {step.tool}</span>
                                    </div>
                                    <pre className="whitespace-pre-wrap text-gray-400 font-mono text-[10px] overflow-x-auto p-1 bg-black/20 rounded">
                                        {JSON.stringify(step.tool_input, null, 2)}
                                    </pre>
                                    {step.observation && (
                                        <div className="mt-1 text-gray-500 italic border-t border-gray-800/50 pt-1">
                                            Stop: {step.observation.slice(0, 100)}...
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </details>
                </div>
            )}

            <div className={cn(
                "flex max-w-[90%] rounded-2xl p-3 shadow-sm text-sm backdrop-blur-sm",
                message.role === 'user'
                    ? "bg-emerald-600/90 text-white rounded-tr-sm"
                    : "bg-gray-800/80 text-gray-100 rounded-tl-sm border border-gray-700/50"
            )}>
                 <div className="whitespace-pre-wrap leading-relaxed markdown-content">
                    <ReactMarkdown
                        components={{
                            a: ({node, ...props}) => <a {...props} className="text-emerald-400 hover:underline" target="_blank" rel="noopener noreferrer" />,
                            strong: ({node, ...props}) => <strong {...props} className="font-bold text-white" />,
                            ul: ({node, ...props}) => <ul {...props} className="list-disc leading-relaxed list-inside my-1" />,
                            ol: ({node, ...props}) => <ol {...props} className="list-decimal leading-relaxed list-inside my-1" />,
                            li: ({node, ...props}) => <li {...props} className="ml-1" />,
                            code: ({node, className, children, ...props}) => {
                                const match = /language-(\w+)/.exec(className || '')
                                return match ? (
                                    <code className={`${className} bg-black/30 rounded px-1 py-0.5`} {...props}>
                                        {children}
                                    </code>
                                ) : (
                                    <code className="bg-black/30 rounded px-1 py-0.5 text-xs font-mono" {...props}>
                                        {children}
                                    </code>
                                )
                            },
                            pre: ({node, ...props}) => <pre {...props} className="bg-black/30 p-2 rounded-lg overflow-x-auto my-2 text-xs font-mono border border-white/10" />
                        }}
                    >
                        {message.content}
                    </ReactMarkdown>
                </div>
            </div>
        </div>
    );
}
