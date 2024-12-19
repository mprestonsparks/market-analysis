#!/usr/bin/env node

const { TaskDecomposition } = require('./.project/status/task-decomposition.js');
const { GitHubAPI } = require('./.github/github.js');
const { Logger } = require('./.github/logger.js');

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
    main().catch(error => {
        console.error(error);
        process.exit(1);
    });
}

module.exports = { main };
