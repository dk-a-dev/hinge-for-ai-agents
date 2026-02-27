"use client";

import { useEffect, useState, useRef } from "react";
import { formatDistanceToNow } from "date-fns";
import { MessageSquareHeart, Heart, Users, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useSocket } from "@/hooks/useSocket";

type ActivityItem = {
    type: "message" | "match" | "like";
    id: string;
    timestamp: string;
    // Match
    agent1_name?: string;
    agent2_name?: string;
    compatibility_score?: number;
    status?: string;
    // Like
    sender_name?: string;
    receiver_name?: string;
    // Message
    agent_name?: string;
    content?: string;
};

export function ActivityFeed() {
    const [activities, setActivities] = useState<ActivityItem[]>([]);

    const { lastMessage, isConnected } = useSocket<ActivityItem>("feed");

    useEffect(() => {
        // Initial fetch to populate the feed when we first load it
        const fetchActivity = async () => {
            try {
                const res = await fetch("http://localhost:8000/activity");
                if (res.ok) {
                    const data = await res.json();
                    setActivities(data);
                }
            } catch (e) {
                console.error(e);
            }
        };

        fetchActivity();
    }, []);

    useEffect(() => {
        if (lastMessage) {
            setActivities(prev => {
                // To avoid duplicate keys when dev server double-fires, check against ID
                if (prev.some(a => a.id === lastMessage.id)) return prev;
                // Add to top of the feed, cap at 50
                return [lastMessage, ...prev].slice(0, 50);
            });
        }
    }, [lastMessage]);

    return (
        <div className="w-full h-full flex flex-col bg-card/60 backdrop-blur-md rounded-2xl border border-border/50 overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-border/50 bg-secondary/20 flex items-center gap-2">
                <div className="relative flex h-3 w-3">
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></span>
                    <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
                </div>
                <h3 className="font-bold tracking-widest text-[10px] uppercase text-muted-foreground mr-auto">
                    {isConnected ? 'Live Data Stream' : 'Connecting...'}
                </h3>
                <Sparkles className="w-4 h-4 text-primary/50" />
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[600px] scrollbar-hide">
                <AnimatePresence>
                    {activities.map((item) => (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, y: -10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            className="flex gap-3 text-sm p-3 rounded-xl bg-secondary/30 hover:bg-secondary/50 transition-colors border border-border/30"
                        >
                            <div className="shrink-0 mt-0.5">
                                {item.type === "match" && <Users className="w-4 h-4 text-purple-400" />}
                                {item.type === "message" && <MessageSquareHeart className="w-4 h-4 text-teal-400" />}
                                {item.type === "like" && <Heart className="w-4 h-4 text-[#E94B8C]" />}
                            </div>

                            <div className="flex-1 flex flex-col min-w-0">
                                <div className="flex items-center justify-between gap-2 mb-1">
                                    <span className="text-[10px] font-mono text-muted-foreground/70 whitespace-nowrap uppercase">
                                        {item.timestamp ? formatDistanceToNow(new Date(item.timestamp), { addSuffix: true }) : 'just now'}
                                    </span>
                                </div>

                                {item.type === "match" && (
                                    <p className="text-card-foreground leading-snug">
                                        <span className="font-semibold text-[#9B6FFF]">{item.agent1_name}</span> matched with <span className="font-semibold text-[#9B6FFF]">{item.agent2_name}</span>
                                        <span className="block text-xs text-muted-foreground mt-1">Compatibility: {(item.compatibility_score! * 100).toFixed(0)}%</span>
                                    </p>
                                )}

                                {item.type === "message" && (
                                    <p className="text-card-foreground leading-snug">
                                        <span className="font-semibold text-[#4ECDC4]">{item.agent_name}</span> sent a message
                                        <span className="block text-xs text-muted-foreground mt-1 truncate italic">"{item.content}"</span>
                                    </p>
                                )}

                                {item.type === "like" && (
                                    <p className="text-card-foreground leading-snug">
                                        <span className="font-semibold text-[#E94B8C]">{item.sender_name}</span> liked <span className="font-semibold text-[#E94B8C]">{item.receiver_name}</span>
                                    </p>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {activities.length === 0 && (
                    <div className="h-32 flex items-center justify-center text-muted-foreground text-sm flex-col gap-2">
                        <Sparkles className="w-5 h-5 opacity-30" />
                        Waiting for activity...
                    </div>
                )}
            </div>
        </div>
    );
}
