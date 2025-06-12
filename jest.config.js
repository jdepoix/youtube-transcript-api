module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  clearMocks: true, // Automatically clear mock calls and instances between every test
  coverageProvider: 'v8', // or 'babel'
  testMatch: ['**/tests/**/*.test.ts'], // Pattern to discover test files
  moduleNameMapper: {
    // If you have path aliases in tsconfig.json, map them here
    // Example: '^@/(.*)$': '<rootDir>/src/$1'
  },
  // setupFilesAfterEnv: ['./tests/setup.ts'], // If you have a setup file
};
