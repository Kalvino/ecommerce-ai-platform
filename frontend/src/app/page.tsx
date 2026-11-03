'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface MessageLog {
  sender: 'user' | 'ai';
  text: string;
}

export default function AgentChatDashboard() {
  const [messages, setMessages] = useState<MessageLog[]>([]);
  const [inputMsg, setInputMsg] = useState('');
  const [activeNode, setActiveNode] = useState<string>('idle');
  const [isStreaming, setIsStreaming] = useState(false);
  
  // Test parameters mirroring our PostgreSQL seeded account records
  const userEmail = "alex@example.com";
  const threadId = "session_user_abc_123";
  const scrollRef = useRef<HTMLDivElement>(null);

  // Automatically keeps the message container scrolled down as new text arrives
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeNode]);

  const triggerAgentWorkflow = async () => {
    if (!inputMsg.trim() || isStreaming) return;

    const currentPrompt = inputMsg;
    setInputMsg('');
    setMessages(prev => [...prev, { sender: 'user', text: currentPrompt }]);
    setIsStreaming(true);
    setActiveNode('router');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: currentPrompt, email: userEmail, threadId }),
      });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let currentAiResponse = '';

      // Continuous loop reading server data chunks off the wire asynchronously
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const rawTextChunks = decoder.decode(value, { stream: true });
        const dataLines = rawTextChunks.split('\n\n');

        for (const line of dataLines) {
          if (line.startsWith('data: ')) {
            const cleanJsonString = line.replace('data: ', '').trim();
            if (!cleanJsonString) continue;

            try {
              const parsedPayload = JSON.parse(cleanJsonString);

              if (parsedPayload.event === 'node_update') {
                setActiveNode(parsedPayload.node);
              } else if (parsedPayload.event === 'text_chunk') {
                currentAiResponse = parsedPayload.content;
                setMessages(prev => {
                  const filtered = prev.filter(m => m.text !== currentAiResponse);
                  return [...filtered, { sender: 'ai', text: currentAiResponse }];
                });
              } else if (parsedPayload.event === 'workflow_complete') {
                setActiveNode('idle');
              }
            } catch (e) {
              // Gracefully pass over fragmented or splitting string bytes
            }
          }
        }
      }
    } catch (error) {
      console.error("Streaming transaction error:", error);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row h-screen bg-slate-950 text-slate-100 p-4 gap-4">
      {/* LEFT ASPECT: Real-time Multi-Agent Execution Visualizer */}
      <Card className="w-full md:w-1/3 bg-slate-900 border-slate-800 text-slate-100 flex flex-col">
        <CardHeader>
          <CardTitle className="text-xl font-bold flex items-center gap-2">
            🕸️ Agent Execution Monitor
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col gap-4">
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
            <span className="text-sm text-slate-400">Target Session User:</span>
            <Badge variant="outline" className="text-emerald-400 border-emerald-950">{userEmail}</Badge>
          </div>

          <div className="flex-1 flex flex-col justify-center gap-3">
            {[
              { id: 'router', name: '🧠 Router Node', desc: 'Parses customer prompt intent to identify optimal execution paths.' },
              { id: 'account_ops', name: '📦 Account Operations Node', desc: 'Executes live PostgreSQL queries to retrieve transaction lists.' },
              { id: 'rag_specialist', name: '📜 RAG Specialist Node', desc: 'Queries enterprise logistics and return policy documentation maps.' },
              { id: 'inspector', name: '🛡️ Inspector Guardrail Node', desc: 'Runs self-correction safety checks to protect against hallucinations.' }
            ].map((node) => (
              <div 
                key={node.id}
                className={`p-4 rounded-xl border transition-all duration-300 ${
                  activeNode === node.id 
                    ? 'bg-indigo-950/40 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.2)] scale-[1.02]' 
                    : 'bg-slate-950/50 border-slate-800 opacity-60'
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <h3 className="font-semibold text-sm">{node.name}</h3>
                  {activeNode === node.id && (
                    <Badge className="bg-indigo-600 animate-pulse text-[10px]">Processing...</Badge>
                  )}
                </div>
                <p className="text-xs text-slate-400">{node.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* RIGHT ASPECT: Conversational Interface Canvas */}
      <Card className="flex-1 bg-slate-900 border-slate-800 text-slate-100 flex flex-col h-full">
        <CardHeader className="border-b border-slate-800">
          <CardTitle className="text-lg flex items-center justify-between">
            <span>💬 Logistics Concierge Desk</span>
            {isStreaming && <span className="text-xs text-indigo-400 animate-pulse">Live stream channel open...</span>}
          </CardTitle>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col p-4 overflow-hidden">
          <ScrollArea className="flex-1 pr-4 mb-4">
            <div className="flex flex-col gap-3">
              {messages.length === 0 && (
                <div className="text-center text-slate-500 text-sm mt-12">
                  No active messages. Ask your local framework:<br />
                  <span className="text-indigo-400 font-medium italic">"Can you check the status of my active orders?"</span>
                </div>
              )}
              {messages.map((msg, i) => (
                <div 
                  key={i} 
                  className={`flex flex-col max-w-[85%] rounded-2xl p-4 text-sm ${
                    msg.sender === 'user' 
                      ? 'bg-slate-800 text-slate-100 self-end rounded-br-none' 
                      : 'bg-indigo-950/60 border border-indigo-900/50 text-indigo-100 self-start rounded-bl-none whitespace-pre-wrap'
                  }`}
                >
                  <span className="text-[10px] text-indigo-400 mb-1 block font-mono">
                    {msg.sender === 'user' ? 'CUSTOMER' : 'LOGISTICS_AI'}
                  </span>
                  {msg.text}
                </div>
              ))}
              <div ref={scrollRef} />
            </div>
          </ScrollArea>

          <div className="flex gap-2 bg-slate-950 p-2 rounded-xl border border-slate-800">
            <Input 
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && triggerAgentWorkflow()}
              placeholder="Inquire about delivery history, refund policies, tracking statuses..."
              className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-slate-100 placeholder-slate-500"
              disabled={isStreaming}
            />
            <Button 
              onClick={triggerAgentWorkflow}
              disabled={isStreaming || !inputMsg.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-5 rounded-lg transition-all"
            >
              Send
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
