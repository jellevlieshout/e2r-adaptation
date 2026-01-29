import type {
  User,
  AuthResponse,
  AdaptationResponse,
  FigurativeExpression,
} from "./types";

// =============================================================================
// Mock User Data
// =============================================================================

export const mockUser: User = {
  id: "user-1",
  email: "demo@example.com",
  name: "Demo User",
};

export const mockAuthResponse: AuthResponse = {
  user: mockUser,
  token: "mock-jwt-token-12345",
};

// =============================================================================
// Mock Figurative Expressions
// =============================================================================

// Note: startIndex and endIndex must match exact character positions in originalText
const mockExpressions: Record<string, FigurativeExpression[]> = {
  // "When I arrived at the party, I tried to break the ice with my new colleagues. I reminded myself that time is money, so I made the most of every conversation."
  adaptation1: [
    {
      id: "expr-1",
      type: "idiom",
      original: "break the ice",
      startIndex: 40,
      endIndex: 53,
      explanation:
        "This phrase means to start a conversation or make people feel more comfortable in a social situation.",
      simplifiedVersion: "start talking to someone new",
    },
    {
      id: "expr-2",
      type: "conceptual_metaphor",
      original: "time is money",
      startIndex: 101,
      endIndex: 114,
      explanation:
        "This phrase uses the conceptual metaphor TIME IS MONEY, where we understand time in terms of a valuable resource that can be spent, saved, or wasted.",
      simplifiedVersion: "time is valuable",
    },
  ],
  // "It took me a while to grasp the concept, but eventually the idea clicked."
  adaptation2: [
    {
      id: "expr-3",
      type: "conceptual_metaphor",
      original: "grasp the concept",
      startIndex: 22,
      endIndex: 39,
      explanation:
        "This uses the conceptual metaphor UNDERSTANDING IS GRASPING, where we understand ideas as physical objects we can hold.",
      simplifiedVersion: "understand the idea",
    },
  ],
  // "Please don't spill the beans about the surprise party. Don't let the cat out of the bag!"
  adaptation3: [
    {
      id: "expr-4",
      type: "idiom",
      original: "spill the beans",
      startIndex: 13,
      endIndex: 28,
      explanation:
        "This phrase means to reveal a secret or share information that was supposed to be kept private.",
      simplifiedVersion: "tell the secret",
    },
    {
      id: "expr-5",
      type: "idiom",
      original: "let the cat out of the bag",
      startIndex: 61,
      endIndex: 87,
      explanation:
        "This idiom means to accidentally reveal a secret.",
      simplifiedVersion: "accidentally reveal the secret",
    },
  ],
  // "Life is a journey, and we all have our own paths to follow."
  adaptation4: [
    {
      id: "expr-6",
      type: "conceptual_metaphor",
      original: "Life is a journey",
      startIndex: 0,
      endIndex: 17,
      explanation:
        "This uses the conceptual metaphor LIFE IS A JOURNEY, where life events are understood as traveling along a path with destinations and obstacles.",
      simplifiedVersion: "life has many stages and experiences",
    },
  ],
};

// =============================================================================
// Mock Adaptations
// =============================================================================

export const mockAdaptations: AdaptationResponse[] = [
  {
    id: "adaptation1",
    originalText:
      "When I arrived at the party, I tried to break the ice with my new colleagues. I reminded myself that time is money, so I made the most of every conversation.",
    adaptedText:
      "When I arrived at the party, I tried to start talking to someone new with my new colleagues. I reminded myself that time is valuable, so I made the most of every conversation.",
    expressions: mockExpressions.adaptation1,
    createdAt: "2024-01-20T14:30:00Z",
  },
  {
    id: "adaptation2",
    originalText:
      "It took me a while to grasp the concept, but eventually the idea clicked.",
    adaptedText:
      "It took me a while to understand the idea, but eventually I understood.",
    expressions: mockExpressions.adaptation2,
    createdAt: "2024-01-19T10:15:00Z",
  },
  {
    id: "adaptation3",
    originalText:
      "Please don't spill the beans about the surprise party. Don't let the cat out of the bag!",
    adaptedText:
      "Please don't tell the secret about the surprise party. Don't accidentally reveal the secret!",
    expressions: mockExpressions.adaptation3,
    createdAt: "2024-01-18T16:45:00Z",
  },
  {
    id: "adaptation4",
    originalText:
      "Life is a journey, and we all have our own paths to follow.",
    adaptedText:
      "Life has many stages and experiences, and we all have our own paths to follow.",
    expressions: mockExpressions.adaptation4,
    createdAt: "2024-01-17T09:00:00Z",
  },
];

// =============================================================================
// Mock API Helpers
// =============================================================================

// Simulate network delay
export function delay(ms: number = 500): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Generate a new adaptation from input text (simulated)
export function generateMockAdaptation(text: string): AdaptationResponse {
  const id = `adaptation-${Date.now()}`;
  const expressions: FigurativeExpression[] = [];
  let adaptedText = text;

  // Simple pattern matching for common figurative expressions
  const patterns: Array<{
    regex: RegExp;
    type: FigurativeExpression["type"];
    explanation: string;
    simplified: string;
  }> = [
    {
      regex: /break the ice/gi,
      type: "idiom",
      explanation: "This means to start a conversation or reduce tension.",
      simplified: "start a conversation",
    },
    {
      regex: /piece of cake/gi,
      type: "idiom",
      explanation: "This means something is very easy to do.",
      simplified: "very easy",
    },
    {
      regex: /hit the nail on the head/gi,
      type: "idiom",
      explanation: "This means to be exactly right about something.",
      simplified: "exactly right",
    },
    {
      regex: /spill the beans/gi,
      type: "idiom",
      explanation: "This means to reveal a secret.",
      simplified: "reveal the secret",
    },
    {
      regex: /time is money/gi,
      type: "conceptual_metaphor",
      explanation: "This uses the conceptual metaphor TIME IS MONEY, understanding time as a valuable resource.",
      simplified: "time is valuable",
    },
    {
      regex: /life is a journey/gi,
      type: "conceptual_metaphor",
      explanation: "This uses the conceptual metaphor LIFE IS A JOURNEY, understanding life as traveling a path.",
      simplified: "life has many experiences",
    },
    {
      regex: /grasp the (concept|idea)/gi,
      type: "conceptual_metaphor",
      explanation: "This uses the conceptual metaphor UNDERSTANDING IS GRASPING, understanding ideas as objects we hold.",
      simplified: "understand the $1",
    },
  ];

  patterns.forEach((pattern) => {
    let match;
    while ((match = pattern.regex.exec(text)) !== null) {
      const original = match[0];
      let simplified = pattern.simplified;

      // Handle regex groups for similes
      if (match[1] && match[2]) {
        simplified = simplified.replace("$1", match[1]);
      }

      expressions.push({
        id: `expr-${Date.now()}-${expressions.length}`,
        type: pattern.type,
        original,
        startIndex: match.index,
        endIndex: match.index + original.length,
        explanation: pattern.explanation,
        simplifiedVersion: simplified,
      });

      adaptedText = adaptedText.replace(original, simplified);
    }
  });

  return {
    id,
    originalText: text,
    adaptedText,
    expressions,
    createdAt: new Date().toISOString(),
  };
}
