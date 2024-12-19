class Logger {
    constructor(module) {
        this.module = module;
    }

    formatMessage(level, message) {
        const timestamp = new Date().toISOString();
        return `[${timestamp}] ${level.toUpperCase()} [${this.module}] ${message}`;
    }

    info(message) {
        console.log(this.formatMessage('info', message));
    }

    warn(message) {
        console.warn(this.formatMessage('warn', message));
    }

    error(message) {
        console.error(this.formatMessage('error', message));
    }

    debug(message) {
        if (process.env.DEBUG === 'true') {
            console.debug(this.formatMessage('debug', message));
        }
    }
}

module.exports = { Logger };
