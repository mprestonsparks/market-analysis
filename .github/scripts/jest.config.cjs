module.exports = {
    testEnvironment: 'node',
    collectCoverage: true,
    coverageDirectory: 'coverage',
    coverageReporters: ['json', 'lcov', 'text', 'clover'],
    testMatch: ['**/*.test.js'],
    verbose: true
};
