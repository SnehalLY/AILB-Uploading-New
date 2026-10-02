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

export const api = {
  async login(data: LoginData) {
    const response = await fetch('/api/login', {
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
