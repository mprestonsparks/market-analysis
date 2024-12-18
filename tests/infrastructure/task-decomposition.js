const { readFileSync } = require('fs');
const yaml = require('js-yaml');
const { Logger } = require('./logger');

const logger = new Logger('task-decomposition');

class TaskDecomposition {
    constructor(yamlPath) {
        this.yamlPath = yamlPath;
        this.data = yaml.load(readFileSync(yamlPath, 'utf8'));
    }

    async syncWithGitHub(github) {
        const tasks = this.data.next_available_tasks;
        for (const task of tasks) {
            const issue = await github.createIssue(task.name, this.generateIssueBody(task));
            logger.info(`Created issue #${issue.number} for task ${task.name}`);
        }
    }

    generateIssueBody(task) {
        let body = task.description + '\n\n';

        if (task.blocking && task.blocking.length > 0) {
            body += '### Blocks\n';
            for (const id of task.blocking) {
                body += `- #${id}\n`;
            }
        }

        if (task.blocked_by && task.blocked_by.length > 0) {
            body += '\n### Blocked By\n';
            for (const id of task.blocked_by) {
                body += `- #${id}\n`;
            }
        }

        return body;
    }
}

module.exports = { TaskDecomposition };
