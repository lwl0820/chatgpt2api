import assert from "node:assert/strict";
import test from "node:test";

import { getImageSelectionCandidatePrompt } from "../src/lib/image-selection-prompt.ts";

test("uses candidate generation prompt before session prompt", () => {
  assert.equal(
    getImageSelectionCandidatePrompt({ prompt: "cat" }, { prompt: "dog" }),
    "cat",
  );
});

test("falls back to session prompt for historical candidates", () => {
  assert.equal(
    getImageSelectionCandidatePrompt({}, { prompt: "dog" }),
    "dog",
  );
});

test("falls back to session prompt for blank candidate prompt", () => {
  assert.equal(
    getImageSelectionCandidatePrompt({ prompt: "   " }, { prompt: "dog" }),
    "dog",
  );
});
