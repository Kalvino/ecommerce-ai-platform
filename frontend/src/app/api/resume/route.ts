import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { threadId, approved } = await req.json();

    const BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';
    const API_SECRET = process.env.INTERNAL_API_SECRET;

    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/agent/resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-API-Key': API_SECRET || '',
      },
      body: JSON.stringify({ thread_id: threadId, approved }),
    });

    const data = await backendResponse.json();
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (error) {
    console.error('BFF Resume Proxy Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
