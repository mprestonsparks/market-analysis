const { readFileSync } = require('fs');
const yaml = require('js-yaml');
const Ajv = require('ajv');

class YamlValidator {
    constructor(schemaPath) {
        const schema = JSON.parse(readFileSync(schemaPath, 'utf8'));
        this.ajv = new Ajv();
        this.validate = this.ajv.compile(schema);
    }

    validateFile(filePath) {
        try {
            const content = readFileSync(filePath, 'utf8');
            const data = yaml.load(content);
            
            if (!data) {
                return {
                    valid: false,
                    errors: [{ message: 'Empty or invalid YAML' }]
                };
            }

            const valid = this.validate(data);
            return {
                valid,
                errors: this.validate.errors || []
            };
        } catch (error) {
            return {
                valid: false,
                errors: [{ message: error.message }]
            };
        }
    }

    validateTaskIds(data) {
        const taskIds = new Set();
        const errors = [];

        for (const task of data.next_available_tasks) {
            if (taskIds.has(task.id)) {
                errors.push({ message: `Duplicate task ID: ${task.id}` });
            }
            taskIds.add(task.id);
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

function validateYaml(filePath) {
    const content = readFileSync(filePath, 'utf8');
    const data = yaml.load(content);
    
    if (!data || typeof data !== 'object') {
        throw new Error('Invalid YAML: Document must be a valid object');
    }
    return true;
}

module.exports = { YamlValidator, validateYaml };
