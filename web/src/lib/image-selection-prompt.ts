export type ImageSelectionPromptCandidate = {
  prompt?: string;
};

export type ImageSelectionPromptSession = {
  prompt: string;
};

export function getImageSelectionCandidatePrompt(
  candidate: ImageSelectionPromptCandidate,
  session: ImageSelectionPromptSession,
) {
  return candidate.prompt?.trim() || session.prompt;
}
