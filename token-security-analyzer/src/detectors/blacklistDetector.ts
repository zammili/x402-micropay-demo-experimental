// blacklistDetector.ts

// Import necessary libraries or modules if needed

// A function to detect if a token is in the blacklist
function isTokenBlacklisted(token: string, blacklist: string[]): boolean {
    return blacklist.includes(token);
}

// Example usage
const blacklist = ['badToken1', 'badToken2', 'badToken3'];
const tokenToCheck = 'someToken';
const isBlacklisted = isTokenBlacklisted(tokenToCheck, blacklist);

if (isBlacklisted) {
    console.log(`Token ${tokenToCheck} is blacklisted.`);
} else {
    console.log(`Token ${tokenToCheck} is not blacklisted.`);
}