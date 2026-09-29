import { assertSafeEndpoint, getCoordinatorUrl } from '../config';

interface LoginData {
  username: string;
  password: string;
  question: string;
  answer_sets: string;
  difficulty: number;
  overall_marks: number;
  author: string;
  topic: string;
  question_bank: string;
  num_blanks: number;
}

async function getNextBackendUrl(): Promise<string> {
  const coordinatorUrl = await getCoordinatorUrl();
  const response = await fetch(`${coordinatorUrl}/next-backend`);
  if (!response.ok) throw new Error('Failed to get backend URL');
  const data: unknown = await response.json();
  if (!data || typeof data !== 'object' || !("backend_url" in data) || typeof data.backend_url !== 'string') {
    throw new Error('Coordinator returned an invalid backend URL');
  }
  return assertSafeEndpoint('coordinator backend_url', data.backend_url);
}

export const api = {
  async login(data: LoginData) {
    const backendUrl = await getNextBackendUrl();
    const response = await fetch(`${backendUrl}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(result.error || 'Failed to upload question');
    }
    return { success: true, message: result.message ?? null, data: result };
  },
};
