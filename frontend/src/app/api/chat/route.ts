import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { message, email, threadId } = await req.json();

    const BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';
    const API_SECRET = process.env.INTERNAL_API_SECRET;

    // Secure server-to-server POST connection to your active Python FastAPI instance
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/agent/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API-Key': API_SECRET || '',
      },
      body: JSON.stringify({
        message,
        user_email: email,
        thread_id: threadId,
      }),
    });

    if (!backendResponse.ok) {
      return NextResponse.json(
        { error: `FastAPI responded with status code: ${backendResponse.status}` },
        { status: backendResponse.status }
      );
    }

    // Return a text/event-stream response to cleanly pass incoming server events to the client
    return new NextResponse(backendResponse.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Next.js BFF Gateway Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
