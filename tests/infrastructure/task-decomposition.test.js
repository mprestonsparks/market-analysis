const { TaskDecomposition } = require('./task-decomposition');
const { GitHubAPI } = require('./github');
const fs = require('fs');
const yaml = require('js-yaml');

jest.mock('fs');
jest.mock('js-yaml');
jest.mock('./github');

describe('TaskDecomposition', () => {
    let taskDecomposition;
    let mockGitHub;

    beforeEach(() => {
        const mockYamlContent = {
            next_available_tasks: [
                {
                    id: 1,
                    name: 'Task 1',
                    description: 'Test Description',
                    blocking: [2],
                    blocked_by: [3]
                }
            ]
        };

        fs.readFileSync.mockReturnValue('mock yaml content');
        yaml.load.mockReturnValue(mockYamlContent);

        mockGitHub = new GitHubAPI();
        mockGitHub.createIssue = jest.fn().mockReturnValue('https://github.com/owner/repo/issues/1');

        taskDecomposition = new TaskDecomposition('test.yaml');
    });

    test('should sync tasks with GitHub', async () => {
        await taskDecomposition.syncWithGitHub(mockGitHub);
        expect(mockGitHub.createIssue).toHaveBeenCalledWith(
            'Task 1',
            expect.stringContaining('Test Description')
        );
    });

    test('should generate correct issue body', () => {
        const task = {
            description: 'Test Description',
            blocking: [2],
            blocked_by: [3]
        };
        const body = taskDecomposition.generateIssueBody(task);
        expect(body).toContain('Test Description');
        expect(body).toContain('### Blocks\n- #2');
        expect(body).toContain('### Blocked By\n- #3');
    });

    test('should handle tasks without dependencies', () => {
        const task = {
            description: 'Simple Task'
        };
        const body = taskDecomposition.generateIssueBody(task);
        expect(body).toContain('Simple Task');
        expect(body).not.toContain('### Blocks');
        expect(body).not.toContain('### Blocked By');
    });
});
