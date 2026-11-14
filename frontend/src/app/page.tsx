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
  
  // Human-in-the-Loop interactive states
  const [isIntercepted, setIsIntercepted] = useState(false);
  const [interceptReason, setInterceptReason] = useState('');
  const [supervisorDirective, setSupervisorDirective] = useState('');

  const userEmail = "alex@example.com";
  const threadId = "session_user_abc_123";
  const scrollRef = useRef<HTMLDivElement>(null);

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
    setIsIntercepted(false);

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

              if (parsedPayload.event === 'approval_required') {
                setIsIntercepted(true);
                setInterceptReason(parsedPayload.reason || 'High-risk operations flagged.');
                setActiveNode('account_ops'); 
                setIsStreaming(false);
                return; 
              } else if (parsedPayload.event === 'node_update') {
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
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
    } finally {
      if (!isIntercepted) setIsStreaming(false);
    }
  };

  const handleSupervisorDecision = async (approved: boolean) => {
    setIsIntercepted(false);
    setIsStreaming(true);
    
    setMessages(prev => [
      ...prev, 
      { 
        sender: 'ai', 
        text: approved 
          ? `🔄 Resuming operation with supervisor authorization...${supervisorDirective ? `\nDirective Injected: "${supervisorDirective}"` : ''}` 
          : "❌ Transaction rejected by supervisor." 
      }
    ]);

    try {
      const response = await fetch('/api/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          threadId, 
          approved,
          directive: supervisorDirective.trim() || undefined
        }),
      });

      if (response.ok && approved) {
        setMessages(prev => [...prev, { sender: 'ai', text: "✅ System records successfully updated with your request." }]);
      }
    } catch (error) {
      console.error("Error executing supervisor response:", error);
    } finally {
      setIsStreaming(false);
      setActiveNode('idle');
      setSupervisorDirective('');
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
                    ? isIntercepted 
                      ? 'bg-amber-950/40 border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.2)]'
                      : 'bg-indigo-950/40 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.2)]' 
                    : 'bg-slate-950/50 border-slate-800 opacity-60'
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <h3 className="font-semibold text-sm">{node.name}</h3>
                  {activeNode === node.id && (
                    <Badge className={isIntercepted ? "bg-amber-600 animate-pulse text-[10px]" : "bg-indigo-600 animate-pulse text-[10px]"}>
                      {isIntercepted ? "FROZEN / HOLD" : "Processing..."}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-slate-400">{node.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* RIGHT ASPECT: Conversational Interface Canvas */}
      <Card className="flex-1 bg-slate-900 border-slate-800 text-slate-100 flex flex-col h-full overflow-hidden">
        <CardHeader className="border-b border-slate-800">
          <CardTitle className="text-lg flex items-center justify-between">
            <span>💬 Logistics Concierge Desk</span>
            {isStreaming && <span className="text-xs text-indigo-400 animate-pulse">Live stream channel open...</span>}
          </CardTitle>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col p-4 min-h-0 overflow-hidden relative">
          
          {/* INTERCEPT OVERLAY CONTROL MAPPING PANEL */}
          {isIntercepted && (
            <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4 md:p-8">
              <Card className="w-full max-w-4xl bg-slate-900 border-amber-500/40 shadow-2xl text-slate-100 flex flex-col max-h-[85vh] overflow-hidden">
                
                <CardHeader className="border-b border-slate-800 bg-slate-950/50 px-6 py-4 flex flex-row items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-950/60 rounded-lg border border-amber-500/30 text-amber-500 animate-pulse">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                    </div>
                    <div>
                      <CardTitle className="text-base font-bold text-amber-500">Human-in-the-Loop Gatekeeper Intercept</CardTitle>
                      <p className="text-[11px] text-slate-400 font-mono mt-0.5">GRAPH_THREAD: {threadId}</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="bg-amber-950/30 text-amber-400 border-amber-900 px-2 py-0.5 font-mono text-[10px]">STATE_HOLD_ACTIVE</Badge>
                </CardHeader>

                <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
                  {/* LEFT COLUMN: Telemetry & Payload Context */}
                  <div className="w-full md:w-1/2 p-6 border-b md:border-b-0 md:border-r border-slate-800 overflow-y-auto space-y-4">
                    <div>
                      <span className="text-[10px] font-mono text-slate-500 tracking-wider block mb-1">INTERCEPT TRIGGER CAUSE</span>
                      <div className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800 font-sans">
                        {interceptReason}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <span className="text-[10px] font-mono text-slate-500 tracking-wider block">MUTATION TARGET TELEMETRY</span>
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-2">
                        <div className="flex justify-between border-b border-slate-900 pb-1">
                          <span className="text-slate-500">target_node:</span>
                          <span className="text-indigo-400">account_ops</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-900 pb-1">
                          <span className="text-slate-500">operation_risk:</span>
                          <span className="text-rose-400 font-bold">CRITICAL_WRITE</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-900 pb-1">
                          <span className="text-slate-500">auth_scope:</span>
                          <span className="text-slate-300">address_modification</span>
                        </div>
                        <div className="flex justify-between pt-0.5">
                          <span className="text-slate-500">database_driver:</span>
                          <span className="text-emerald-500">psycopg_async</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* RIGHT COLUMN: Terminal Transition Logs & Input Adjustments */}
                  <div className="w-full md:w-1/2 p-6 bg-slate-950/20 flex flex-col justify-between overflow-y-auto">
                    <div className="space-y-4">
                      <div>
                        <span className="text-[10px] font-mono text-slate-500 tracking-wider block mb-1">PRE-INTERCEPT RUNTIME LOGS</span>
                        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-400 space-y-1 max-h-36 overflow-y-auto">
                          <p className="text-slate-600">[RUN] ENGINE_START → State initialized.</p>
                          <p className="text-indigo-400">[OK] NODE_COMPLETE → router (parsed intent)</p>
                          <p className="text-amber-500">[HALT] INTERRUPT_BEFORE → account_ops triggered</p>
                          <p className="text-rose-500 font-bold">[WAIT] SYSTEM_FREEZE → Awaiting supervisor keys...</p>
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] font-mono text-slate-500 tracking-wider block mb-1">OPTIONAL INTERVENTION INPUT</span>
                        <textarea
                          value={supervisorDirective}
                          onChange={(e) => setSupervisorDirective(e.target.value)}
                          placeholder="Type directives to inject into the thread state here... (e.g., 'Verify loyalty tier before executing modification')"
                          className="w-full h-16 bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-amber-500/50 resize-none font-mono"
                        />
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-2 pt-4 border-t border-slate-800/60 mt-4">
                      <Button
                        variant="outline"
                        onClick={() => handleSupervisorDecision(false)}
                        className="flex-1 border-slate-800 bg-slate-900 text-slate-300 hover:bg-rose-950/20 hover:text-rose-400 hover:border-rose-900 font-mono text-xs h-9 transition-all"
                      >
                        🛑 Deny & Abort
                      </Button>
                      <Button
                        onClick={() => handleSupervisorDecision(true)}
                        className="flex-1 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold font-mono text-xs h-9 transition-all shadow-lg shadow-amber-950/20"
                      >
                        ⚡ Authorize Run
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}

          <ScrollArea className="flex-1 h-full pr-4 mb-4">
            <div className="flex flex-col gap-3">
              {messages.length === 0 && (
                <div className="text-center text-slate-500 text-sm mt-12 space-y-2">
                  <p>No active messages. Ask your local framework:</p>
                  <p className="text-indigo-400 font-medium italic">"What is your standard return policy?"</p>
                  <p className="text-slate-600 text-xs">Or trigger a high-risk hold interrupt step using:</p>
                  <p className="text-amber-500 font-medium italic">"I want to change my current order delivery address"</p>
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
              placeholder={isIntercepted ? "System frozen pending supervisor action..." : "Inquire or request transaction adjustments..."}
              className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-slate-100 placeholder-slate-500"
              disabled={isStreaming || isIntercepted}
            />
            <Button 
              onClick={triggerAgentWorkflow}
              disabled={isStreaming || isIntercepted || !inputMsg.trim()}
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
