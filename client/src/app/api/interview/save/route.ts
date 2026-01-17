import { NextRequest, NextResponse } from "next/server";
import { saveInterviewToDb } from "@/lib/db/operations";
import { InterviewDetails } from "@/lib/interview";
import { verifyToken } from "@/lib/auth";

export async function POST(req: NextRequest) {
  try {
    const data: InterviewDetails = await req.json();
    
    if (!process.env.MONGO_URI) {
      console.error("MONGO_URI is not defined");
      return NextResponse.json({ error: "Server configuration error" }, { status: 500 });
    }

    // Verify token
    const authHeader = req.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: "Missing or invalid authorization header" }, { status: 401 });
    }

    const token = authHeader.split(' ')[1];
    try {
      verifyToken(token);
    } catch (err: any) {
      console.error('Token verification failed:', err.message);
      return NextResponse.json({ error: "Unauthorized: " + err.message }, { status: 403 });
    }

    console.log('Saving interview to DB...');
    const result = await saveInterviewToDb(data, process.env.MONGO_URI);
    console.log('Interview saved successfully');

    return NextResponse.json(result);
  } catch (err) {
    console.error('Error saving interview:', err);
    return NextResponse.json({ 
      error: "Error saving interview", 
      details: err instanceof Error ? err.message : String(err) 
    }, { status: 500 });
  }
}
