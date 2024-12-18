const { expect, test, describe } = require('@jest/globals');
const { YamlValidator, validateYaml } = require('./yaml.js');
const { readFileSync } = require('fs');
const yaml = require('js-yaml');

jest.mock('fs');
jest.mock('js-yaml');

describe('YamlValidator', () => {
    const mockSchema = {
        type: 'object',
        required: ['next_available_tasks'],
        properties: {
            next_available_tasks: {
                type: 'array',
                items: {
                    type: 'object',
                    required: ['id', 'name', 'status'],
                    properties: {
                        id: { type: 'number' },
                        name: { type: 'string' },
                        status: { type: 'string' }
                    }
                }
            }
        }
    };

    beforeEach(() => {
        jest.resetAllMocks();
        readFileSync.mockReturnValueOnce(JSON.stringify(mockSchema));
    });

    test('should validate valid YAML', () => {
        const validator = new YamlValidator('schema.json');
        const validYaml = `
next_available_tasks:
  - id: 1
    name: Task 1
    status: ready
  - id: 2
    name: Task 2
    status: blocked
`;
        const validData = {
            next_available_tasks: [
                { id: 1, name: 'Task 1', status: 'ready' },
                { id: 2, name: 'Task 2', status: 'blocked' }
            ]
        };

        readFileSync.mockReturnValueOnce(validYaml);
        yaml.load.mockReturnValueOnce(validData);
        
        const result = validator.validateFile('test.yaml');
        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
    });

    test('should catch invalid YAML', () => {
        const validator = new YamlValidator('schema.json');
        const invalidYaml = `
next_available_tasks:
  - id: "not a number"
    name: Task 1
    status: ready
`;
        const invalidData = {
            next_available_tasks: [
                { id: "not a number", name: 'Task 1', status: 'ready' }
            ]
        };

        readFileSync.mockReturnValueOnce(invalidYaml);
        yaml.load.mockReturnValueOnce(invalidData);
        
        const result = validator.validateFile('test.yaml');
        expect(result.valid).toBe(false);
        expect(result.errors).toHaveLength(1);
    });

    test('should validate task IDs', () => {
        const validator = new YamlValidator('schema.json');
        const data = {
            next_available_tasks: [
                { id: 1, name: 'Task 1', status: 'ready', blocking: [2] },
                { id: 2, name: 'Task 2', status: 'blocked', blocked_by: [1] }
            ]
        };
        const result = validator.validateTaskIds(data);
        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
    });

    test('should catch duplicate task IDs', () => {
        const validator = new YamlValidator('schema.json');
        const data = {
            next_available_tasks: [
                { id: 1, name: 'Task 1', status: 'ready' },
                { id: 1, name: 'Task 2', status: 'blocked' }
            ]
        };
        const result = validator.validateTaskIds(data);
        expect(result.valid).toBe(false);
        expect(result.errors[0].message).toContain('Duplicate task ID: 1');
    });
});

describe('YAML Validation', () => {
    beforeEach(() => {
        jest.resetAllMocks();
    });

    test('should validate correct YAML', () => {
        const mockYaml = {
            next_available_tasks: [
                {
                    id: 1,
                    name: 'Task 1',
                    description: 'Description 1',
                    blocking: [2]
                }
            ]
        };

        readFileSync.mockReturnValueOnce('mock yaml content');
        yaml.load.mockReturnValueOnce(mockYaml);

        expect(() => validateYaml('test.yaml')).not.toThrow();
    });

    test('should reject invalid YAML', () => {
        readFileSync.mockReturnValueOnce('mock yaml content');
        yaml.load.mockReturnValueOnce(null);

        expect(() => validateYaml('test.yaml')).toThrow('Invalid YAML: Document must be a valid object');
    });
});
