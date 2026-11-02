import test from 'node:test';
import assert from 'node:assert/strict';

// Helper reproduction of cn logic
function clsx(...inputs) {
  return inputs
    .flat(Infinity)
    .filter(Boolean)
    .join(' ');
}

// Helper reproduction of formatRelativeTime
function formatRelativeTime(dateStr, mockNow) {
  const d = new Date(dateStr);
  const now = mockNow ? new Date(mockNow) : new Date();
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'just now';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays}d ago`;
  }

  return d.toISOString().split('T')[0];
}

// Helper citation extractor (used in Ask SMRITIX page)
function extractCitations(text) {
  const matches = text.match(/\[(\d+)\]/g);
  if (!matches) return [];
  const indices = matches.map(m => parseInt(m.replace(/[\[\]]/g, ''), 10));
  return Array.from(new Set(indices));
}

// RRF rank calculation
function calculateRRFScore(rankBM25, rankVector, k = 60) {
  const scoreBM25 = rankBM25 !== null ? 1 / (k + rankBM25) : 0;
  const scoreVector = rankVector !== null ? 1 / (k + rankVector) : 0;
  return scoreBM25 + scoreVector;
}

test('clsx utility merges conditional classes and ignores falsy values', () => {
  const result = clsx('btn', true && 'btn-primary', false && 'btn-disabled', null, undefined, 'shadow-md');
  assert.equal(result, 'btn btn-primary shadow-md');
});

test('formatRelativeTime correctly formats relative thresholds', () => {
  const baseNow = '2026-10-26T12:00:00.000Z';

  // 15 seconds ago -> just now
  assert.equal(formatRelativeTime('2026-10-26T11:59:45.000Z', baseNow), 'just now');

  // 5 minutes ago
  assert.equal(formatRelativeTime('2026-10-26T11:55:00.000Z', baseNow), '5m ago');

  // 3 hours ago
  assert.equal(formatRelativeTime('2026-10-26T09:00:00.000Z', baseNow), '3h ago');

  // 2 days ago
  assert.equal(formatRelativeTime('2026-10-24T12:00:00.000Z', baseNow), '2d ago');
});

test('extractCitations extracts and deduplicates citation tokens', () => {
  const answer = 'Quantum computers use superposition [1] and entanglement [2]. As noted in [1], error correction is vital.';
  const citations = extractCitations(answer);
  assert.deepEqual(citations, [1, 2]);
});

test('calculateRRFScore correctly blends BM25 and Vector search ranks', () => {
  // Rank 1 in both BM25 and Vector
  const topScore = calculateRRFScore(1, 1, 60);
  assert.equal(topScore, 2 / 61);

  // Rank 1 in BM25, no vector match
  const partialScore = calculateRRFScore(1, null, 60);
  assert.equal(partialScore, 1 / 61);

  assert.ok(topScore > partialScore);
});
