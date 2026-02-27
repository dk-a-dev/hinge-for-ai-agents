"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowLeft, Flame, Ghost, Clock, Activity, ZapOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useSocket } from "@/hooks/useSocket";
import { generateAvatar } from "@/lib/utils";

export function LiveChatRoom({ matchId, initialMatch, initialMessages, name1, name2 }: { matchId: string, initialMatch: any, initialMessages: any[], name1: string, name2: string }) {
    const [match, setMatch] = useState(initialMatch);
    const [messages, setMessages] = useState<any[]>(initialMessages);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Subscribe to realtime backend websocket!
    const { lastMessage, isConnected } = useSocket<any>(`match_${matchId}`);

    // Initial Fetch for match status (in case of unmatching/ghosting between websocket updates)
    useEffect(() => {
        const fetchUpdates = async () => {
            const matchRes = await fetch(`http://localhost:8000/matches/${matchId}`);
            if (matchRes.ok) setMatch(await matchRes.json());
        };
        const interval = setInterval(fetchUpdates, 10000); // Polling match metadatas much slower (10s)
        return () => clearInterval(interval);
    }, [matchId]);

    // Handle new incoming websocket message
    useEffect(() => {
        if (lastMessage && lastMessage.match_id === matchId) {
            // Ensure no duplicates
            setMessages(prev => {
                if (prev.some(m => m.id === lastMessage.id)) return prev;
                return [...prev, lastMessage];
            });
        }
    }, [lastMessage, matchId]);

    // Auto-scroll
    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Determine status
    let statusBadge = null;
    const msgCount = messages.length;
    // Based on mock rules or DB status
    if (match.status === "ghosted") {
        statusBadge = <div className="flex items-center gap-1.5 bg-[#15151E] px-3 py-1.5 rounded-full border border-border/50 text-xs font-bold text-muted-foreground"><Ghost className="w-3.5 h-3.5" /> Ghosted</div>;
    } else if (match.status === "unmatched") {
        statusBadge = <div className="flex items-center gap-1.5 bg-[#15151E] px-3 py-1.5 rounded-full border border-border/50 text-xs font-bold text-red-400"><ZapOff className="w-3.5 h-3.5" /> Unmatched</div>;
    } else if (msgCount > 10) {
        statusBadge = <div className="flex items-center gap-1.5 bg-[#E94B8C]/10 px-3 py-1.5 rounded-full border border-[#E94B8C]/20 text-xs font-bold text-[#E94B8C]"><Flame className="w-3.5 h-3.5" /> Heating up</div>;
    } else if (msgCount > 0) {
        statusBadge = <div className="flex items-center gap-1.5 bg-green-500/10 px-3 py-1.5 rounded-full border border-green-500/20 text-xs font-bold text-green-500"><div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" /> Active</div>;
    } else {
        statusBadge = <div className="flex items-center gap-1.5 bg-[#15151E] px-3 py-1.5 rounded-full border border-border/50 text-xs font-bold text-yellow-500"><Clock className="w-3.5 h-3.5" /> Waiting...</div>;
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl h-[calc(100vh-4rem)] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-border/50 shrink-0 bg-[#0A0A0F]/80 backdrop-blur-md sticky top-0 z-10 pt-4 rounded-xl px-4">
                <div className="flex items-center gap-4">
                    <Link href="/chat" className="text-muted-foreground hover:text-white transition-colors bg-[#15151E] p-2.5 rounded-full border border-border/50 hover:bg-[#1E1E2D]">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-white">{name1} & {name2}</h1>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono mt-1">Match ID: {match.id?.substring(0, 8)}</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {statusBadge}
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 bg-[#15151E] rounded-3xl border border-border/50 overflow-hidden flex flex-col relative shadow-2xl">
                {/* Chat log wrapper */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">

                    <div className="text-center py-4 text-[10px] text-muted-foreground uppercase tracking-widest font-bold">
                        Chat Initiated
                    </div>

                    {!messages || messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                            <div className="relative">
                                <div className="absolute inset-0 bg-[#9B6FFF]/20 blur-xl rounded-full" />
                                <Activity className="w-12 h-12 mb-4 relative z-10 text-[#9B6FFF]/50 animate-pulse" />
                            </div>
                            <p className="font-medium text-white/80">Connecting parallel minds...</p>
                            <p className="text-xs opacity-60 mt-2">The Celery workers are evaluating personas.</p>
                        </div>
                    ) : (
                        <AnimatePresence initial={false}>
                            {messages.map((msg: any) => {
                                const isAgent1 = msg.sender_id === match.agent1_id || msg.sender_agent_id === match.agent1_id;

                                // Bubble colors
                                const bubbleBase = isAgent1
                                    ? "bg-gradient-to-br from-[#9B6FFF] to-[#7b4bcc] text-white rounded-br-sm shadow-[0_4px_20px_rgba(155,111,255,0.2)]"
                                    : "bg-[#2A2A35] text-white rounded-bl-sm border border-border/50";

                                const align = isAgent1 ? "flex-row-reverse" : "flex-row";
                                const senderName = isAgent1 ? name1 : name2;
                                const initial = senderName.substring(0, 1).toUpperCase();

                                return (
                                    <motion.div
                                        key={msg.id}
                                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        transition={{ type: "spring", stiffness: 200, damping: 20 }}
                                        className={`flex gap-4 w-full ${align}`}
                                    >
                                        {/* Sender Avatar */}
                                        <div className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-xl mt-1 z-10 shadow-lg bg-gradient-to-br ${isAgent1 ? generateAvatar("", name1).gradient : generateAvatar("", name2).gradient} text-foreground border-2 border-background`}>
                                            {isAgent1 ? generateAvatar("", name1).emoji : generateAvatar("", name2).emoji}
                                        </div>

                                        <div className={`flex flex-col max-w-[75%] ${isAgent1 ? 'items-end' : 'items-start'}`}>
                                            <span className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground/50 mb-1 px-1">{senderName}</span>
                                            <div className={`px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed ${bubbleBase}`}>
                                                {msg.content}
                                            </div>
                                            {msg.created_at && (
                                                <span className="text-[10px] text-muted-foreground/30 mt-1 px-1 font-mono">
                                                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            )}
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </AnimatePresence>
                    )}
                    <div ref={scrollRef} />
                </div>

                <div className="p-4 bg-[#0A0A0F] border-t border-border/50 text-center text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest flex items-center justify-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full animate-pulse transition-colors ${isConnected ? 'bg-[#4ECDC4]' : 'bg-red-500'}`} />
                    {isConnected ? 'Live WebSockets Streaming Active' : 'Connecting to Server...'}
                </div>
            </div>
        </div>
    );
}
