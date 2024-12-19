module.exports = {
  testEnvironment: 'node',
  roots: ['<rootDir>/..'],
  moduleFileExtensions: ['js', 'json'],
  testMatch: [
    '<rootDir>/../**/*.test.js',
    '<rootDir>/../.github/**/*.test.js',
    '<rootDir>/../.project/**/*.test.js'
  ],
  transform: {
    '^.+\\.js$': 'babel-jest'
  },
  moduleDirectories: ['node_modules', '<rootDir>/../node_modules'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/../$1',
    '^\\./task-decomposition$': '<rootDir>/../.project/status/task-decomposition.js',
    '^\\./github$': '<rootDir>/../.github/github.js'
  },
  setupFilesAfterEnv: ['<rootDir>/../jest.setup.js'],
  haste: {
    forceNodeFilesystemAPI: true,
    throwOnModuleCollision: false
  }
};
