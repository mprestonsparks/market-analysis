#!/usr/bin/env node

const { TaskDecomposition } = require('./task-decomposition.js');
const { GitHubAPI } = require('./github.js');
const { Logger } = require('./logger.js');

const logger = new Logger('sync');

async function main() {
    try {
        const github = new GitHubAPI();
        const taskDecomposition = new TaskDecomposition('.project/status/DEVELOPMENT_STATUS.yaml');
        await taskDecomposition.syncWithGitHub(github);
        logger.info('Successfully synchronized tasks with GitHub');
    } catch (error) {
        logger.error(`Sync failed: ${error.message}`);
        throw error;
    }
}

if (require.main === module) {
    main();
}

module.exports = { main };
