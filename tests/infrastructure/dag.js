const { readFileSync } = require('fs');
const yaml = require('js-yaml');

class DAG {
    constructor() {
        this.nodes = new Set();
        this.edges = new Map();
        this.incomingEdges = new Map();
    }

    addNode(node) {
        if (this.nodes.has(node)) {
            throw new Error(`Node ${node} already exists`);
        }
        this.nodes.add(node);
        this.edges.set(node, new Set());
        this.incomingEdges.set(node, new Set());
    }

    addEdge(from, to) {
        if (!this.nodes.has(from)) {
            throw new Error(`Node ${from} does not exist`);
        }
        if (!this.nodes.has(to)) {
            throw new Error(`Node ${to} does not exist`);
        }
        this.edges.get(from).add(to);
        this.incomingEdges.get(to).add(from);
    }

    hasCycle() {
        const visited = new Set();
        const recursionStack = new Set();

        const dfs = (node) => {
            visited.add(node);
            recursionStack.add(node);

            for (const neighbor of this.edges.get(node)) {
                if (!visited.has(neighbor)) {
                    if (dfs(neighbor)) {
                        return true;
                    }
                } else if (recursionStack.has(neighbor)) {
                    return true;
                }
            }

            recursionStack.delete(node);
            return false;
        };

        for (const node of this.nodes) {
            if (!visited.has(node)) {
                if (dfs(node)) {
                    return true;
                }
            }
        }

        return false;
    }

    getRoots() {
        const roots = new Set();
        for (const node of this.nodes) {
            if (this.incomingEdges.get(node).size === 0) {
                roots.add(node);
            }
        }
        return roots;
    }

    getLeaves() {
        const leaves = new Set();
        for (const node of this.nodes) {
            if (this.edges.get(node).size === 0) {
                leaves.add(node);
            }
        }
        return leaves;
    }

    getAllNodes() {
        return Array.from(this.nodes);
    }

    getOutgoingEdges(node) {
        return Array.from(this.edges.get(node));
    }

    getIncomingEdges(node) {
        return Array.from(this.incomingEdges.get(node) || []);
    }

    static fromYaml(yamlPath) {
        const data = yaml.load(readFileSync(yamlPath, 'utf8'));
        const dag = new DAG();

        // Add all nodes first
        for (const task of data.next_available_tasks) {
            dag.addNode(task.id);
        }

        // Then add edges
        for (const task of data.next_available_tasks) {
            if (task.blocking) {
                for (const blockedId of task.blocking) {
                    dag.addEdge(task.id, blockedId);
                }
            }
            if (task.blocked_by) {
                for (const blockerId of task.blocked_by) {
                    dag.addEdge(blockerId, task.id);
                }
            }
        }

        return dag;
    }
}

module.exports = { DAG };
