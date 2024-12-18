import { expect, test, describe, jest } from '@jest/globals';
import { Logger } from './logger.js';

describe('Logger', () => {
    let consoleSpy;
    const originalDebug = process.env.DEBUG;

    beforeEach(() => {
        consoleSpy = {
            log: jest.spyOn(console, 'log').mockImplementation(),
            warn: jest.spyOn(console, 'warn').mockImplementation(),
            error: jest.spyOn(console, 'error').mockImplementation(),
            debug: jest.spyOn(console, 'debug').mockImplementation()
        };
    });

    afterEach(() => {
        jest.restoreAllMocks();
        process.env.DEBUG = originalDebug;
    });

    test('should log info messages', () => {
        const logger = new Logger('test');
        logger.info('test message');
        expect(consoleSpy.log).toHaveBeenCalledWith(
            expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T.*\] INFO \[test\] test message/)
        );
    });

    test('should log warning messages', () => {
        const logger = new Logger('test');
        logger.warn('test warning');
        expect(consoleSpy.warn).toHaveBeenCalledWith(
            expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T.*\] WARN \[test\] test warning/)
        );
    });

    test('should log error messages', () => {
        const logger = new Logger('test');
        logger.error('test error');
        expect(consoleSpy.error).toHaveBeenCalledWith(
            expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T.*\] ERROR \[test\] test error/)
        );
    });

    test('should log debug messages only when DEBUG is set', () => {
        const logger = new Logger('test');
        
        process.env.DEBUG = '';
        logger.debug('test debug');
        expect(consoleSpy.debug).not.toHaveBeenCalled();

        process.env.DEBUG = 'true';
        logger.debug('test debug');
        expect(consoleSpy.debug).toHaveBeenCalledWith(
            expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T.*\] DEBUG \[test\] test debug/)
        );
    });
});
