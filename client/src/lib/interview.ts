export interface InterviewDetails {
  user_id: string;
  job_id: string;
  transcript: Array<{ role: 'ai' | 'user'; text: string }>;
  created_at: Date;
  updated_at: Date;
  id: string;
  transport_used: string;
  voice_id: string;
  token_used: number;
  max_token: number;
  event_logs: Array<any>;
  coins_used: number;
  max_coins: number;
  tokens_per_coin?: number;
  session_id: string;
}

export async function saveInterview(details: InterviewDetails) {
  const authToken = localStorage.getItem('authToken');
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const res = await fetch('/api/interview/save', {
    method: 'POST',
    headers,
    body: JSON.stringify(details),
  });
  
  const data = await res.json();
  
  if (!res.ok) {
    // Throw error with status and message for proper handling
    const error: any = new Error(data.error || 'Failed to save interview');
    error.status = res.status;
    error.data = data;
    throw error;
  }
  
  return data;
}