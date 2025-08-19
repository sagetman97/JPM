const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function calculateNeeds(data: Record<string, any>) {
  const response = await fetch(`${API_BASE_URL}/api/calculate-needs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to calculate needs');
  }
  return response.json();
}

export async function fetchProductFAQ(question: string) {
  const response = await fetch(`${API_BASE_URL}/api/product-faq`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch FAQ answer');
  }
  return response.json();
}

export async function runScenarioPlan(base: Record<string, any>, scenarios: Record<string, any>[]) {
  const response = await fetch(`${API_BASE_URL}/api/scenario`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ base, scenarios }),
  });
  if (!response.ok) {
    throw new Error('Failed to run scenario plan');
  }
  return response.json();
} 