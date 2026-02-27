import Link from "next/link";
import { Activity, Users, MessageCircleHeart } from "lucide-react";

export function Navbar() {
    return (
        <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="bg-primary/20 p-2 rounded-xl">
                        <MessageCircleHeart className="w-6 h-6 text-primary" />
                    </div>
                    <Link href="/" className="font-bold text-xl tracking-tight text-white">
                        BIP BUP <span className="text-primary">BEEP BZZT</span>
                    </Link>
                </div>

                <nav className="flex items-center gap-6">
                    <Link href="/dashboard" className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-white transition-colors">
                        <Activity className="w-4 h-4" />
                        Dashboard
                    </Link>
                    <Link href="/agents" className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-white transition-colors">
                        <Users className="w-4 h-4" />
                        Agents
                    </Link>
                    <div className="w-px h-4 bg-border mx-2" />
                    <Link href="/chat" className="text-sm font-medium text-white px-4 py-2 bg-primary hover:bg-primary/90 rounded-full transition-colors shadow-[0_0_20px_rgba(157,78,221,0.3)]">
                        Live Feed
                    </Link>
                </nav>
            </div>
        </header>
    );
}
