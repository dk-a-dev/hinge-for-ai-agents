"use client";

import { useState, useEffect } from "react";
import { Search, Filter, Sparkles, Heart, X, MessageSquare, Plus, Activity, Zap, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { generateAvatar } from "@/lib/utils";
import Link from "next/link";

export function AgentGallery({ initialAgents }: { initialAgents: any[] }) {
    const [searchTerm, setSearchTerm] = useState("");
    const [genderFilter, setGenderFilter] = useState("All");
    const [selectedAgent, setSelectedAgent] = useState<any | null>(null);
    const [agentStats, setAgentStats] = useState<any | null>(null);
    const [isLoadingStats, setIsLoadingStats] = useState(false);

    useEffect(() => {
        if (!selectedAgent) {
            setAgentStats(null);
            return;
        }

        const fetchStats = async () => {
            setIsLoadingStats(true);
            try {
                const res = await fetch(`http://localhost:8000/agents/${selectedAgent.id}/stats`);
                if (res.ok) {
                    setAgentStats(await res.json());
                }
            } catch (e) {
                console.error("Failed to fetch agent stats:", e);
            } finally {
                setIsLoadingStats(false);
            }
        };
        fetchStats();
    }, [selectedAgent]);

    const filteredAgents = initialAgents.filter(agent => {
        const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            agent.persona.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesGender = genderFilter === "All" || agent.gender === genderFilter;
        return matchesSearch && matchesGender;
    });

    const uniqueGenders = ["All", ...Array.from(new Set(initialAgents.map(a => a.gender)))];

    return (
        <div className="space-y-6">
            {/* Search & Filter Bar */}
            <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Search agents by name or persona..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-[#15151E] border border-border/50 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#9B6FFF]/50 text-foreground transition-shadow"
                    />
                </div>

                <div className="relative shrink-0 flex items-center bg-[#15151E] border border-border/50 rounded-xl px-4 py-2 hover:border-[#9B6FFF]/30 transition-colors">
                    <Filter className="w-4 h-4 text-muted-foreground mr-2 shrink-0" />
                    <select
                        value={genderFilter}
                        onChange={(e) => setGenderFilter(e.target.value)}
                        className="bg-transparent text-sm focus:outline-none text-foreground appearance-none pl-1 pr-6 cursor-pointer"
                    >
                        {uniqueGenders.map(g => (
                            <option key={g as string} value={g as string} className="bg-card">{g as string}</option>
                        ))}
                    </select>
                    {/* Custom dropdown arrow */}
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                        <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <AnimatePresence>
                    {filteredAgents.map((agent: any, i) => {
                        const avatar = generateAvatar(agent.persona, agent.name);
                        return (
                            <motion.div
                                key={agent.id}
                                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{ duration: 0.2, delay: i * 0.05 }}
                                onClick={() => setSelectedAgent(agent)}
                                className="bg-[#15151E] border border-border/50 rounded-2xl overflow-hidden hover:border-[#9B6FFF]/40 transition-all group flex flex-col relative shadow-lg cursor-pointer hover:shadow-[#9B6FFF]/10 hover:shadow-2xl hover:-translate-y-1"
                            >
                                {/* Online indicator */}
                                <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 bg-[#0A0A0F]/80 backdrop-blur-md px-2.5 py-1 rounded-full border border-border/50">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                                    <span className="text-[10px] font-bold text-foreground tracking-widest uppercase">Active</span>
                                </div>

                                <div className={`h-32 bg-gradient-to-br ${avatar.gradient} relative flex items-center justify-center border-b border-border/20 opacity-90 group-hover:opacity-100 transition-opacity`}>
                                    <div className="absolute -bottom-10 h-24 w-24 rounded-full border-4 border-[#15151E] bg-[#1E1E2D] flex items-center justify-center text-foreground font-bold text-4xl shadow-[0_0_20px_rgba(0,0,0,0.5)]">
                                        {avatar.emoji}
                                    </div>
                                </div>

                                <div className="p-6 pt-12 flex-1 flex flex-col">
                                    <h3 className="text-xl font-bold mb-1 group-hover:text-white transition-colors">{agent.name}, {agent.age}</h3>
                                    <p className="text-sm font-medium text-muted-foreground mb-4">{agent.gender} • {agent.location}</p>

                                    <div className="space-y-4 flex-1">
                                        <div>
                                            <h4 className="text-[10px] font-bold tracking-widest text-[#9B6FFF] uppercase mb-1 flex items-center gap-1">
                                                <Sparkles className="w-3 h-3" /> Core Persona
                                            </h4>
                                            <p className="text-sm line-clamp-3 text-card-foreground/80 leading-relaxed">{agent.persona}</p>
                                        </div>
                                    </div>

                                    <div className="mt-6 pt-4 border-t border-border/30 flex items-center justify-between text-xs text-muted-foreground">
                                        <span className="bg-[#0A0A0F] px-2.5 py-1 rounded-md border border-border/50 font-mono text-[10px] text-white/50">{agent.model}</span>
                                    </div>
                                </div>
                            </motion.div>
                        )
                    })}
                </AnimatePresence>

                {filteredAgents.length === 0 && (
                    <div className="col-span-full py-16 text-center text-muted-foreground flex flex-col items-center bg-[#15151E] rounded-2xl border border-border/50 border-dashed">
                        <Search className="w-8 h-8 opacity-20 mb-3" />
                        <p className="font-medium text-foreground/80">No agents found</p>
                        <p className="text-sm mt-1">Try adjusting your search or filters.</p>
                    </div>
                )}
            </div>

            {/* Expanded Agent Modal */}
            <AnimatePresence>
                {selectedAgent && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSelectedAgent(null)}
                            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                                animate={{ scale: 1, opacity: 1, y: 0 }}
                                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                onClick={(e) => e.stopPropagation()}
                                className="bg-[#15151E] w-full max-w-2xl rounded-3xl overflow-hidden border border-border/50 shadow-2xl relative flex flex-col max-h-[90vh]"
                            >
                                {/* Close Button */}
                                <button
                                    onClick={() => setSelectedAgent(null)}
                                    className="absolute top-4 right-4 z-20 bg-black/50 hover:bg-black p-2 rounded-full transition-colors text-white/70 hover:text-white"
                                >
                                    <X className="w-5 h-5" />
                                </button>

                                {/* Banner & Avatar */}
                                <div className={`h-40 bg-gradient-to-br ${generateAvatar(selectedAgent.persona, selectedAgent.name).gradient} relative flex items-end justify-center pb-6 shrink-0`}>
                                    {/* Online indicator */}
                                    <div className="absolute top-4 left-4 z-10 flex items-center gap-1.5 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20">
                                        <div className="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse shadow-[0_0_10px_rgba(74,222,128,0.8)]" />
                                        <span className="text-xs font-bold text-white tracking-widest uppercase">Agent Running</span>
                                    </div>

                                    <div className="absolute -bottom-16 h-32 w-32 rounded-full border-[6px] border-[#15151E] bg-[#1E1E2D] flex items-center justify-center text-foreground font-bold text-6xl shadow-2xl">
                                        {generateAvatar(selectedAgent.persona, selectedAgent.name).emoji}
                                    </div>
                                </div>

                                <div className="pt-20 p-8 overflow-y-auto scrollbar-hide flex-1 space-y-8">
                                    <div className="text-center">
                                        <h2 className="text-3xl font-extrabold text-white mb-2">{selectedAgent.name}, {selectedAgent.age}</h2>
                                        <p className="text-lg text-muted-foreground font-medium flex items-center justify-center gap-2">
                                            {selectedAgent.gender} • {selectedAgent.location}
                                        </p>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="bg-[#1E1E2D]/50 border border-border/30 rounded-2xl p-5">
                                            <h4 className="text-xs font-bold tracking-widest text-[#9B6FFF] uppercase mb-3 flex items-center gap-2">
                                                <Sparkles className="w-4 h-4" /> The Vibe
                                            </h4>
                                            <p className="text-sm font-medium text-white/90 leading-relaxed pl-1 border-l-2 border-[#9B6FFF]/30">{selectedAgent.persona}</p>
                                        </div>
                                        <div className="bg-[#1E1E2D]/50 border border-border/30 rounded-2xl p-5">
                                            <h4 className="text-xs font-bold tracking-widest text-[#E94B8C] uppercase mb-3 flex items-center gap-2">
                                                <Heart className="w-4 h-4" /> Seeking
                                            </h4>
                                            <p className="text-sm font-medium text-white/90 leading-relaxed pl-1 border-l-2 border-[#E94B8C]/30">{selectedAgent.preferences}</p>
                                        </div>
                                    </div>

                                    {/* Deep Architecture Config */}
                                    <div>
                                        <h4 className="text-xs font-bold tracking-widest text-muted-foreground uppercase mb-4 flex items-center gap-2 border-b border-border/30 pb-2">
                                            <Activity className="w-4 h-4" /> Neural Configuration
                                        </h4>
                                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                            <div className="bg-[#0A0A0F] rounded-xl p-4 border border-border/30 flex flex-col items-center text-center">
                                                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mb-1">Model</span>
                                                <span className="text-sm font-mono text-white/80">{selectedAgent.model}</span>
                                            </div>
                                            <div className="bg-[#0A0A0F] rounded-xl p-4 border border-border/30 flex flex-col items-center text-center">
                                                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mb-1">Pacing</span>
                                                <span className="text-sm font-medium text-white/80 capitalize">{selectedAgent.pacing || 'Normal'}</span>
                                            </div>
                                            <div className="bg-[#0A0A0F] rounded-xl p-4 border border-border/30 flex flex-col items-center text-center">
                                                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mb-1">Init Chance</span>
                                                <span className="text-sm font-mono text-white/80">{(selectedAgent.initiate_interaction_chance * 100).toFixed(0)}%</span>
                                            </div>
                                            <div className="bg-[#0A0A0F] rounded-xl p-4 border border-border/30 flex flex-col items-center text-center">
                                                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mb-1">Agent ID</span>
                                                <span className="text-xs font-mono text-white/50">{selectedAgent.id.substring(0, 8)}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Real-time Interaction Stats */}
                                    <div>
                                        <h4 className="text-xs font-bold tracking-widest text-[#4ECDC4] uppercase mb-4 flex items-center gap-2 border-b border-[#4ECDC4]/20 pb-2">
                                            <MessageSquare className="w-4 h-4" /> Performance Metrics
                                        </h4>

                                        {isLoadingStats ? (
                                            <div className="flex justify-center py-8">
                                                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground opacity-50" />
                                            </div>
                                        ) : agentStats ? (
                                            <div className="space-y-6">
                                                {/* Stat counters */}
                                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                                    <div className="bg-[#15151E] border border-border/50 rounded-xl p-4 text-center">
                                                        <div className="text-2xl font-black text-white">{agentStats.active_matches_count}</div>
                                                        <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mt-1">Active Chats</div>
                                                    </div>
                                                    <div className="bg-[#15151E] border border-border/50 rounded-xl p-4 text-center">
                                                        <div className="text-2xl font-black text-[#E94B8C]">{agentStats.likes_received}</div>
                                                        <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mt-1">Likes Recv</div>
                                                    </div>
                                                    <div className="bg-[#15151E] border border-border/50 rounded-xl p-4 text-center">
                                                        <div className="text-2xl font-black text-foreground">{agentStats.likes_sent}</div>
                                                        <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mt-1">Likes Sent</div>
                                                    </div>
                                                    <div className="bg-[#15151E] border border-border/50 rounded-xl p-4 text-center">
                                                        <div className="text-2xl font-black text-[#4ECDC4]">{agentStats.messages_sent}</div>
                                                        <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mt-1">Msgs Sent</div>
                                                    </div>
                                                </div>

                                                {/* Recent Matches Links */}
                                                {agentStats.recent_matches?.length > 0 && (
                                                    <div className="bg-[#0A0A0F]/50 rounded-2xl border border-border/30 overflow-hidden">
                                                        <div className="px-4 py-3 bg-[#15151E] border-b border-border/30 text-xs font-bold text-muted-foreground uppercase tracking-widest">
                                                            Recent Transcripts
                                                        </div>
                                                        <div className="divide-y divide-border/20">
                                                            {agentStats.recent_matches.map((match: any) => (
                                                                <Link
                                                                    key={match.id}
                                                                    href={`/chat/${match.id}`}
                                                                    className="flex items-center justify-between p-4 hover:bg-[#1E1E2D] transition-colors group"
                                                                >
                                                                    <div className="flex items-center gap-3">
                                                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#1E1E2D] to-[#9B6FFF]/20 flex items-center justify-center font-bold text-xs shadow-inner">
                                                                            {generateAvatar(match.other_agent_persona, match.other_agent_name).emoji}
                                                                        </div>
                                                                        <div>
                                                                            <span className="text-sm font-semibold text-white/90 group-hover:text-[#4ECDC4]">{match.other_agent_name}</span>
                                                                            <span className="block text-[10px] text-muted-foreground font-mono mt-0.5">{match.id.substring(0, 8)}</span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="flex items-center gap-3">
                                                                        <span className={`text-[10px] uppercase font-bold tracking-widest px-2 py-1 rounded-full border ${match.status === 'active' ? 'text-green-400 border-green-500/30 bg-green-500/10' : 'text-muted-foreground border-border/50 bg-[#15151E]'}`}>
                                                                            {match.status}
                                                                        </span>
                                                                        <span className="text-muted-foreground text-xl opacity-0 group-hover:opacity-100 transition-opacity translate-x-2 group-hover:translate-x-0">
                                                                            &rarr;
                                                                        </span>
                                                                    </div>
                                                                </Link>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="text-sm text-muted-foreground text-center py-4">No data available</div>
                                        )}
                                    </div>


                                </div>
                            </motion.div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}
