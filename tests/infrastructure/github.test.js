const { GitHubAPI } = require('./github');
const { execSync } = require('child_process');

jest.mock('child_process');

describe('GitHubAPI', () => {
    let github;
    const issueUrl = 'https://github.com/owner/repo/issues/1';

    beforeEach(() => {
        jest.clearAllMocks();
        execSync.mockReturnValue('');
        github = new GitHubAPI();
    });

    test('should create issue', () => {
        execSync.mockReturnValueOnce(issueUrl);

        const result = github.createIssue('Test Issue', 'Test Body', ['bug']);
        expect(result).toBe(issueUrl);
        expect(execSync).toHaveBeenCalledWith(
            expect.stringContaining('gh issue create'),
            expect.any(Object)
        );
    });

    test('should update issue', () => {
        github.updateIssue(1, {
            state: 'closed',
            title: 'Updated Title',
            body: 'Updated Body',
            labels: ['bug', 'priority']
        });

        expect(execSync).toHaveBeenCalledWith(
            expect.stringContaining('gh issue edit 1'),
            expect.any(Object)
        );
    });

    test('should add comment to issue', () => {
        github.addIssueComment(1, 'Test Comment');

        expect(execSync).toHaveBeenCalledWith(
            expect.stringContaining('gh issue comment 1'),
            expect.any(Object)
        );
    });

    test('should get issue', () => {
        const issueData = {
            number: 1,
            title: 'Test Issue',
            body: 'Test Body',
            state: 'open',
            labels: ['bug']
        };
        execSync.mockReturnValueOnce(JSON.stringify(issueData));

        const result = github.getIssue(1);
        expect(result).toEqual(issueData);
    });

    test('should list issues', () => {
        const issues = [
            { number: 1, title: 'Issue 1', state: 'open', labels: ['bug'] },
            { number: 2, title: 'Issue 2', state: 'closed', labels: ['feature'] }
        ];
        execSync.mockReturnValueOnce(JSON.stringify(issues));

        const result = github.listIssues();
        expect(result).toEqual(issues);
    });
});
