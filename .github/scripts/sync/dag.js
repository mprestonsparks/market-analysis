const fs = require('fs');
const yaml = require('js-yaml');

class DAG {
    constructor() {
        this.nodes = new Map();
        this.edges = new Map();
    }

    addNode(id, data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid node data');
        }
        this.nodes.set(id, data);
        if (!this.edges.has(id)) {
            this.edges.set(id, new Set());
        }
    }

    hasNode(id) {
        return this.nodes.has(id);
    }

    hasEdge(from, to) {
        return this.edges.has(from) && this.edges.get(from).has(to);
    }

    addEdge(from, to) {
        if (!this.nodes.has(from)) {
            throw new Error('Node does not exist: ' + from);
        }
        if (!this.nodes.has(to)) {
            throw new Error('Node does not exist: ' + to);
        }
        if (this._wouldCreateCycle(from, to)) {
            throw new Error('Cycle detected');
        }
        this.edges.get(from).add(to);
    }

    _wouldCreateCycle(from, to) {
        // Check if adding this edge would create a cycle
        const visited = new Set();
        const recursionStack = new Set();

        const hasCycleUtil = (node) => {
            visited.add(node);
            recursionStack.add(node);

            // Temporarily add the new edge
            const neighbors = new Set(this.edges.get(node));
            if (node === from) {
                neighbors.add(to);
            }

            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    if (hasCycleUtil(neighbor)) {
                        return true;
                    }
                } else if (recursionStack.has(neighbor)) {
                    return true;
                }
            }

            recursionStack.delete(node);
            return false;
        };

        return hasCycleUtil(from);
    }

    getNode(id) {
        return this.nodes.get(id);
    }

    getEdges(id) {
        return Array.from(this.edges.get(id) || []);
    }

    getAllNodes() {
        return Array.from(this.nodes.keys());
    }

    async loadFromYaml(filePath) {
        try {
            const content = await fs.promises.readFile(filePath, 'utf8');
            const data = yaml.load(content);
            
            if (!data || !data.tasks) {
                throw new Error('Invalid YAML structure');
            }

            // Clear existing data
            this.nodes.clear();
            this.edges.clear();

            // Add nodes
            for (const [taskId, task] of Object.entries(data.tasks)) {
                this.addNode(taskId, task);
            }

            // Add edges
            for (const [taskId, task] of Object.entries(data.tasks)) {
                if (task.dependencies) {
                    for (const dep of task.dependencies) {
                        this.addEdge(dep, taskId);
                    }
                }
            }
        } catch (error) {
            if (error.code === 'ENOENT') {
                throw new Error('YAML file not found');
            }
            throw error;
        }
    }

    hasCycle() {
        const visited = new Set();
        const recursionStack = new Set();

        const hasCycleUtil = (node) => {
            visited.add(node);
            recursionStack.add(node);

            for (const neighbor of this.edges.get(node)) {
                if (!visited.has(neighbor)) {
                    if (hasCycleUtil(neighbor)) {
                        return true;
                    }
                } else if (recursionStack.has(neighbor)) {
                    return true;
                }
            }

            recursionStack.delete(node);
            return false;
        };

        for (const node of this.nodes.keys()) {
            if (!visited.has(node)) {
                if (hasCycleUtil(node)) {
                    return true;
                }
            }
        }

        return false;
    }

    topologicalSort() {
        if (this.hasCycle()) {
            throw new Error('Cannot perform topological sort on a cyclic graph');
        }

        const visited = new Set();
        const result = [];

        const visit = (node) => {
            if (visited.has(node)) return;
            visited.add(node);

            for (const neighbor of this.edges.get(node)) {
                visit(neighbor);
            }

            result.unshift(node);
        };

        for (const node of this.nodes.keys()) {
            visit(node);
        }

        return result;
    }
}

module.exports = {
    DAG
};
