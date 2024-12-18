// GitHub API integration module
const { Logger } = require('./logger');
const { execSync } = require('child_process');

const logger = new Logger('github');

class GitHubAPI {
    constructor() {
        this.validateGHCLI();
    }

    validateGHCLI() {
        try {
            execSync('gh --version', { stdio: 'ignore' });
        } catch (error) {
            throw new Error('GitHub CLI (gh) is not installed or not in PATH');
        }
    }

    createIssue(title, body, labels = []) {
        try {
            const labelArgs = labels.map(label => `--label "${label}"`).join(' ');
            const command = `gh issue create --title "${title}" --body "${body}" ${labelArgs}`;
            const result = execSync(command, { encoding: 'utf8' });
            logger.info(`Created issue: ${result.trim()}`);
            return result.trim();
        } catch (error) {
            logger.error(`Failed to create issue: ${error.message}`);
            throw error;
        }
    }

    updateIssue(number, { state, title, body, labels } = {}) {
        try {
            const args = [];
            if (state) args.push(`--state "${state}"`);
            if (title) args.push(`--title "${title}"`);
            if (body) args.push(`--body "${body}"`);
            if (labels) args.push(labels.map(label => `--add-label "${label}"`).join(' '));

            const command = `gh issue edit ${number} ${args.join(' ')}`;
            execSync(command, { encoding: 'utf8' });
            logger.info(`Updated issue #${number}`);
        } catch (error) {
            logger.error(`Failed to update issue #${number}: ${error.message}`);
            throw error;
        }
    }

    addIssueComment(number, body) {
        try {
            const command = `gh issue comment ${number} --body "${body}"`;
            execSync(command, { encoding: 'utf8' });
            logger.info(`Added comment to issue #${number}`);
        } catch (error) {
            logger.error(`Failed to add comment to issue #${number}: ${error.message}`);
            throw error;
        }
    }

    getIssue(number) {
        try {
            const command = `gh issue view ${number} --json number,title,body,state,labels`;
            const result = execSync(command, { encoding: 'utf8' });
            return JSON.parse(result);
        } catch (error) {
            logger.error(`Failed to get issue #${number}: ${error.message}`);
            throw error;
        }
    }

    listIssues({ state = 'open', labels = [] } = {}) {
        try {
            const labelQuery = labels.length ? `--label "${labels.join(',')}"` : '';
            const command = `gh issue list --state ${state} ${labelQuery} --json number,title,state,labels`;
            const result = execSync(command, { encoding: 'utf8' });
            return JSON.parse(result);
        } catch (error) {
            logger.error(`Failed to list issues: ${error.message}`);
            throw error;
        }
    }
}

module.exports = { GitHubAPI };
