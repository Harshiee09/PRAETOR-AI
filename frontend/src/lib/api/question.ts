/** Unicode code points match the backend's character limit and preserve Hindi. */
export function countQuestionCharacters(question: string): number {
  return Array.from(question).length;
}

export function normalizeQuestion(question: string): string {
  return question.trim();
}

export function questionValidationMessage(question: unknown): string | null {
  if (typeof question !== "string")
    return "Enter a question in Hindi or English.";
  const length = countQuestionCharacters(normalizeQuestion(question));
  if (length === 0) return "Enter a question in Hindi or English.";
  if (length > 2000) return "Keep your question to 2,000 characters or fewer.";
  return null;
}
