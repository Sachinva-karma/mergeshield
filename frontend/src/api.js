export async function fetchHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) {
      throw new Error(`Health check failed with HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch system health:', err);
    return null;
  }
}

export async function analyzePR(prUrl) {
  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ pr_url: prUrl }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || `Analysis failed with HTTP ${res.status}`);
  }
  return data;
}
