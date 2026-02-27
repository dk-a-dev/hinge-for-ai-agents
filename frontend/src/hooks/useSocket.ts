import { useEffect, useState, useRef } from 'react';

export function useSocket<T>(channel: string) {
    const [lastMessage, setLastMessage] = useState<T | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        // Connect to FastAPI websocket endpoint
        // Using simple ws:// for local dev, wss:// in prod
        const socketUrl = `ws://localhost:8000/ws/${channel}`;
        ws.current = new WebSocket(socketUrl);

        ws.current.onopen = () => {
            console.log(`Connected to channel: ${channel}`);
            setIsConnected(true);
        };

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                // The payload structural is { type: string, data: {} } from our redis listener
                if (data && data.data) {
                    setLastMessage(data.data as T);
                }
            } catch (error) {
                console.error("Failed to parse websocket message", error);
            }
        };

        ws.current.onclose = () => {
            console.log(`Disconnected from channel: ${channel}`);
            setIsConnected(false);
        };

        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [channel]);

    return { lastMessage, isConnected };
}
