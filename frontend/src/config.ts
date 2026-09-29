const blockedEndpointHashes = new Set([
  '0dd5e318c4c92dcd02e4b8160ff0309e9565d324fb3727030bdf9fc5edd3056b',
  '666ee4f9544cc6591c340bc75cc44d5023fc83448206457eeb9dae6f2d7fd80e',
  'dd3305481c77cf85ab058cd172724a8486ab3a4136851883f2ce022687bd4069',
  '6c94d3db6229a1fe93e1174a06b49cda02e87e612e08a7c554df45039f8eb6b4',
  'd2075c3a87c9c337c13561a132d68b99ec9bc54611dd193f1a9791f65edb5c28',
  'f8b52baeb089a58c59c7b1f984d140d2be5be599df550d27c16d5be4ed3917bd',
  '23e42987a13ad4b750974ca4116e6335b3ed523b3531876ed3644e51c124a622',
  'e959eeac4854ff1459ef4926f5ff2c294f886e450def863c4b29273a59119bca',
  '95ecd961eeaef05e42acaf81363761381e0202bc57d68f16387def260d133f60',
  '97ed2289de0402ff0417354e04c8d4a8463fe8a03de0b92832752d71fea3352d',
  '6db932faceed65561111433010fb62c3137602d088f6e696b34cf26dc5fc6216',
  '2fdec184563a4116686814d900f0f6ffc71b47008c061c28b0060b9665c7cf59',
  'f743c7845a512de1f0c6236bde8aad46ec24d85d2a87f1337597fafebb174229',
]);

async function sha256(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

export async function assertSafeEndpoint(variableName: string, value: string): Promise<string> {
  const normalized = value.trim().replace(/\/$/, '').toLowerCase();
  let parsed: URL;
  try {
    parsed = new URL(normalized);
  } catch {
    throw new Error(`${variableName} must be an absolute URL`);
  }
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error(`${variableName} must use HTTP or HTTPS`);
  }
  if (blockedEndpointHashes.has(await sha256(normalized))) {
    throw new Error(`${variableName} points to a blocked legacy production service`);
  }
  return normalized;
}

export async function getCoordinatorUrl(): Promise<string> {
  const configured = import.meta.env.VITE_COORDINATOR_URL;
  if (!configured) {
    throw new Error('VITE_COORDINATOR_URL is required');
  }
  return assertSafeEndpoint('VITE_COORDINATOR_URL', configured);
}
