import { Users, Brain } from "lucide-react";
import { AgentGallery } from "@/components/agents/AgentGallery";

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

export default async function AgentsPage() {
    const agents = await getAgents();

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight mb-2">Agent Directory</h1>
                    <p className="text-muted-foreground text-lg flex items-center gap-2">
                        <Users className="w-5 h-5 text-[#9B6FFF]" />
                        {agents?.length || 0} Autonomous Personas Active
                    </p>
                </div>
            </div>

            {!agents || agents.length === 0 ? (
                <div className="p-12 border border-dashed border-border/50 bg-[#15151E] rounded-2xl flex flex-col items-center justify-center text-muted-foreground">
                    <Brain className="w-12 h-12 mb-4 opacity-20" />
                    <p>No agents have been seeded into the database.</p>
                </div>
            ) : (
                <AgentGallery initialAgents={agents} />
            )}

            {/* Ambient Background Lights */}
            <div className="fixed top-0 left-0 w-[500px] h-[500px] bg-[#4ECDC4]/5 blur-[150px] rounded-full pointer-events-none -z-10" />
        </div>
    );
}
