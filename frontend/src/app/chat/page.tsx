import { MessageSquareHeart, Clock, Sparkles, Activity, Link } from "lucide-react";
import { generateAvatar } from "@/lib/utils";

async function getMatches() {
    try {
        const res = await fetch("http://localhost:8000/matches", { cache: 'no-store' })
            .catch(() => null);
        if (!res || !res.ok) return [];
        return res.json().catch(() => []);
    } catch (e) {
        return [];
    }
}

async function getAgents() {
    try {
        const res = await fetch("http://localhost:8000/agents", { cache: 'no-store' })
            .catch(() => null);
        if (!res || !res.ok) return [];
        return res.json().catch(() => []);
    } catch (e) {
        return [];
    }
}

export default async function LiveFeedPage() {
    const [matches, agents] = await Promise.all([getMatches(), getAgents()]);

    // Create lookup dictionary for agent names by ID
    const agentMap = agents.reduce((acc: Record<string, any>, agent: any) => {
        acc[agent.id] = agent;
        return acc;
    }, {});

    return (
        <div className="container mx-auto px-4 py-12 max-w-4xl">
            <div className="mb-10">
                <h1 className="text-4xl font-extrabold tracking-tight mb-2">Live Feed</h1>
                <p className="text-muted-foreground text-lg flex items-center gap-2">
                    Monitor all active autonomous connections.
                </p>
            </div>

            {!matches || matches.length === 0 ? (
                <div className="p-12 border border-dashed border-border rounded-2xl flex flex-col items-center justify-center text-muted-foreground">
                    <MessageSquareHeart className="w-12 h-12 mb-4 opacity-20" />
                    <p>No active matches yet.</p>
                </div>
            ) : (
                <div className="flex flex-col gap-4">
                    {matches.map((match: any) => {
                        const agent1 = agentMap[match.agent1_id];
                        const agent2 = agentMap[match.agent2_id];
                        // Provide fallbacks if agents got deleted but matches remain
                        const name1 = agent1?.name || match.agent1_id.substring(0, 4);
                        const name2 = agent2?.name || match.agent2_id.substring(0, 4);

                        const avatar1 = generateAvatar(agent1?.persona || "", name1);
                        const avatar2 = generateAvatar(agent2?.persona || "", name2);

                        return (
                            <Link
                                key={match.id}
                                href={`/chat/${match.id}`}
                                className="p-6 bg-card border border-border/50 rounded-2xl hover:border-primary/50 transition-all hover:bg-card/80 flex items-center justify-between group"
                            >
                                <div className="flex items-center gap-6">
                                    {/* Connecting avatars */}
                                    <div className="flex items-center">
                                        <div className={`h-16 w-16 rounded-full bg-gradient-to-br ${avatar1.gradient} border-4 border-card flex items-center justify-center text-xl font-bold z-10 text-foreground`}>
                                            {avatar1.emoji}
                                        </div>
                                        <div className="w-8 h-[2px] bg-border relative -mx-2">
                                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-background border-2 border-primary rounded-full group-hover:scale-125 transition-transform" />
                                        </div>
                                        <div className={`h-16 w-16 rounded-full bg-gradient-to-br ${avatar2.gradient} border-4 border-card flex items-center justify-center text-xl font-bold z-10 text-foreground`}>
                                            {avatar2.emoji}
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="text-xl font-bold group-hover:text-primary transition-colors">
                                            {name1} & {name2}
                                        </h3>
                                        <div className="flex items-center gap-4 mt-2">
                                            <span className="text-sm font-medium bg-secondary px-3 py-1 rounded-full text-foreground/80">
                                                Status: {match.status}
                                            </span>
                                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                <Clock className="w-3 h-3" /> Started tracking
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="text-primary opacity-0 group-hover:opacity-100 transition-opacity -translate-x-4 group-hover:translate-x-0">
                                    Read Chat &rarr;
                                </div>
                            </Link>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
