import { assertSafeEndpoint, getCoordinatorUrl } from '../config';

// Helper to get backend URL from coordinator
async function getNextBackendUrlFromCoordinator(): Promise<string> {
  const coordinatorUrl = await getCoordinatorUrl();
  const response = await fetch(`${coordinatorUrl}/next-backend`);
  if (!response.ok) throw new Error('Failed to get backend URL');
  const data = await response.json();
  if (!data || typeof data.backend_url !== 'string') {
    throw new Error('Coordinator returned an invalid backend URL');
  }
  return assertSafeEndpoint('coordinator backend_url', data.backend_url);
}

// Public key will be fetched from backend
let PUBLIC_KEY: string | null = null;
let KEY_FETCH_TIMESTAMP: number = 0;
const KEY_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

async function fetchPublicKey(forceRefresh: boolean = false) {
    try {
        // Check if we have a cached key that's still valid
        const now = Date.now();
        if (!forceRefresh && PUBLIC_KEY && (now - KEY_FETCH_TIMESTAMP) < KEY_CACHE_DURATION) {
            console.log('Using cached public key');
            return PUBLIC_KEY;
        }

        const API_URL = await getNextBackendUrlFromCoordinator();
        // Add a timestamp to prevent caching issues
        const response = await fetch(`${API_URL}?t=${now}`, {
            method: 'GET',
            mode: 'cors'
        });

        if (!response.ok) {
            console.error('Failed to fetch public key. Status:', response.status);
            throw new Error(`Failed to fetch public key: ${response.status}`);
        }

        const keyText = await response.text();
        // console.log('Raw response from server:', keyText);
        
        // Clean up the key text
        const cleanKey = keyText.trim();
        if (!cleanKey.includes('-----BEGIN PUBLIC KEY-----')) {
            console.error('Invalid public key format received');
            throw new Error('Invalid public key format');
        }
        
        console.log('Successfully fetched public key');
        PUBLIC_KEY = cleanKey;
        KEY_FETCH_TIMESTAMP = now;
        return cleanKey;
    } catch (error) {
        console.error('Error in fetchPublicKey:', error);
        throw error;
    }
}

async function testKeyPair(publicKey: string): Promise<boolean> {
    try {
        console.log('Testing key pair with sample data...');
        const testData = 'test_key_validation';
        
        // Try to encrypt with the public key
        const encrypted = await encryptDataWithKey(testData, publicKey);
        console.log('Test encryption successful, encrypted length:', encrypted.length);
        
        // We can't test decryption here since we don't have the private key
        // but successful encryption is a good sign
        return true;
    } catch (error) {
        console.error('Key pair test failed:', error);
        return false;
    }
}

async function encryptDataWithKey(data: string, publicKeyPem: string): Promise<string> {
    // console.log('Starting encryption of data length:', data.length);

    // Convert PEM to ArrayBuffer
    const pemHeader = '-----BEGIN PUBLIC KEY-----';
    const pemFooter = '-----END PUBLIC KEY-----';
    const pemContents = publicKeyPem
        .replace(pemHeader, '')
        .replace(pemFooter, '')
        .replace(/\s/g, '');
    // console.log('PEM contents length:', pemContents.length);
    
    const binaryDer = atob(pemContents);
    const binaryArray = new Uint8Array(binaryDer.length);
    for (let i = 0; i < binaryDer.length; i++) {
        binaryArray[i] = binaryDer.charCodeAt(i);
    }
    // console.log('Binary array length:', binaryArray.length);

    // Import the public key
    // console.log('Importing public key...');
    const key = await crypto.subtle.importKey(
        'spki',
        binaryArray,
        {
            name: 'RSA-OAEP',
            hash: 'SHA-256',
        },
        false,
        ['encrypt']
    );
    console.log('Public key imported successfully');

    // Encrypt the data
    // console.log('Encrypting data...');
    const encodedData = new TextEncoder().encode(data);
    
    // Ensure data is not too long for RSA-2048
    if (encodedData.length > 190) { // RSA-2048 can encrypt up to 190 bytes with OAEP
        throw new Error(`Data too long for RSA-2048 encryption: ${encodedData.length} bytes (max 190)`);
    }
    
    const encryptedData = await crypto.subtle.encrypt(
        {
            name: 'RSA-OAEP',
            label: new Uint8Array(0) // Explicitly set empty label to match backend
        },
        key,
        encodedData
    );
    // console.log('Data encrypted successfully, encrypted length:', encryptedData.byteLength);

    // Convert to base64
    const base64Result = btoa(String.fromCharCode(...new Uint8Array(encryptedData)));
    // console.log('Base64 result length:', base64Result.length);
    return base64Result;
}

export const encryptData = async (data: string, maxRetries: number = 3): Promise<string> => {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            // console.log(`Encryption attempt ${attempt}/${maxRetries}`);
            
            // Fetch public key (force refresh on retry attempts)
            const shouldForceRefresh = attempt > 1;
            if (!PUBLIC_KEY || shouldForceRefresh) {
                // console.log(`Fetching public key (force refresh: ${shouldForceRefresh})...`);
                await fetchPublicKey(shouldForceRefresh);
            }

            if (!PUBLIC_KEY) {
                throw new Error('Public key not available after fetch');
            }

            // Test the key pair if this is a retry
            if (attempt > 1) {
                const keyValid = await testKeyPair(PUBLIC_KEY);
                if (!keyValid) {
                    // console.log('Key validation failed, trying to fetch fresh key...');
                    PUBLIC_KEY = null; // Force refresh on next iteration
                    continue;
                }
            }

            // Attempt encryption
            const result = await encryptDataWithKey(data, PUBLIC_KEY);
            // console.log(`Encryption successful on attempt ${attempt}`);
            return result;

        } catch (error) {
            console.error(`Encryption attempt ${attempt} failed:`, error);
            lastError = error as Error;
            
            // Clear cached key on error
            PUBLIC_KEY = null;
            KEY_FETCH_TIMESTAMP = 0;
            
            // Wait a bit before retrying (except on last attempt)
            if (attempt < maxRetries) {
                // console.log(`Waiting before retry attempt ${attempt + 1}...`);
                await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
            }
        }
    }

    throw new Error(`Failed to encrypt data after ${maxRetries} attempts. Last error: ${lastError?.message}`);
};

// Utility function to clear cached keys (useful for debugging)
export const clearKeyCache = () => {
    PUBLIC_KEY = null;
    KEY_FETCH_TIMESTAMP = 0;
    console.log('Key cache cleared');
};

// Function to get current key info (for debugging)
export const getKeyInfo = () => {
    return {
        hasKey: !!PUBLIC_KEY,
        fetchTimestamp: KEY_FETCH_TIMESTAMP,
        cacheAge: Date.now() - KEY_FETCH_TIMESTAMP
    };
};
