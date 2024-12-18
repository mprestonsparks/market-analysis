const { main } = require('./index');
const { TaskDecomposition } = require('./task-decomposition');
const { GitHubAPI } = require('./github');

// Mock the dependencies
jest.mock('./task-decomposition');
jest.mock('./github');

describe('Sync Script', () => {
    let mockSyncWithGitHub;
    let mockGitHubAPI;

    beforeEach(() => {
        jest.clearAllMocks();
        mockSyncWithGitHub = jest.fn().mockResolvedValue(undefined);
        mockGitHubAPI = {
            createIssue: jest.fn().mockResolvedValue({ number: 1 }),
            updateIssue: jest.fn().mockResolvedValue(undefined),
            addComment: jest.fn().mockResolvedValue(undefined)
        };

        TaskDecomposition.mockImplementation(() => ({
            syncWithGitHub: mockSyncWithGitHub
        }));

        GitHubAPI.mockImplementation(() => mockGitHubAPI);
    });

    test('should sync tasks with GitHub', async () => {
        await main();
        expect(TaskDecomposition).toHaveBeenCalledWith('.project/status/DEVELOPMENT_STATUS.yaml');
        expect(mockSyncWithGitHub).toHaveBeenCalledWith(mockGitHubAPI);
    });

    test('should handle errors', async () => {
        mockSyncWithGitHub.mockRejectedValueOnce(new Error('Sync failed'));
        await expect(main()).rejects.toThrow('Sync failed');
    });
});
