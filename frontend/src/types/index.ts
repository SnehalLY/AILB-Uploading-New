
// Question types
export interface Answer {
  id: string;
  text: string;
  isCorrect: boolean;
}

export type DifficultyLevel = 'easy' | 'medium' | 'hard' ;

export interface Question {
  id: string;
  text: string;
  answers: Answer[];
  difficultyLevel: DifficultyLevel;
  author: string;
  topic: string;
  questionBankId: string;
}

export interface QuestionFormData {
  text: string;
  answers: Answer[];
  difficultyLevel: DifficultyLevel;
  author: string;
  topic: string;
  questionBankId: string;
}