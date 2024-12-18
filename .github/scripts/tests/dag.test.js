const { DAG } = require('../sync/dag');
const path = require('path');

describe('DAG', () => {
    let dag;

    beforeEach(() => {
        dag = new DAG();
    });

    describe('Node Management', () => {
        test('should add nodes correctly', () => {
            dag.addNode('task1', { id: 'task1', title: 'Task 1' });
            dag.addNode('task2', { id: 'task2', title: 'Task 2' });
            
            expect(dag.hasNode('task1')).toBe(true);
            expect(dag.hasNode('task2')).toBe(true);
            expect(dag.hasNode('task3')).toBe(false);
        });

        test('should handle duplicate node additions', () => {
            dag.addNode('task1', { id: 'task1', title: 'Task 1' });
            dag.addNode('task1', { id: 'task1', title: 'Updated Task 1' });
            
            const node = dag.getNode('task1');
            expect(node.title).toBe('Updated Task 1');
        });
    });

    describe('Edge Management', () => {
        beforeEach(() => {
            dag.addNode('task1', { id: 'task1' });
            dag.addNode('task2', { id: 'task2' });
            dag.addNode('task3', { id: 'task3' });
        });

        test('should add edges correctly', () => {
            dag.addEdge('task1', 'task2');
            
            expect(dag.hasEdge('task1', 'task2')).toBe(true);
            expect(dag.hasEdge('task2', 'task1')).toBe(false);
        });

        test('should detect cycles', () => {
            dag.addEdge('task1', 'task2');
            dag.addEdge('task2', 'task3');
            
            expect(() => dag.addEdge('task3', 'task1')).toThrow('Cycle detected');
        });
    });

    describe('Topological Sort', () => {
        beforeEach(() => {
            dag.addNode('task1', { id: 'task1' });
            dag.addNode('task2', { id: 'task2' });
            dag.addNode('task3', { id: 'task3' });
        });

        test('should return correct order for linear dependencies', () => {
            dag.addEdge('task1', 'task2');
            dag.addEdge('task2', 'task3');
            
            const order = dag.topologicalSort();
            expect(order).toEqual(['task1', 'task2', 'task3']);
        });

        test('should handle parallel tasks', () => {
            dag.addEdge('task1', 'task3');
            dag.addEdge('task2', 'task3');
            
            const order = dag.topologicalSort();
            // Either task1 or task2 can come first, but task3 must be last
            expect(order.length).toBe(3);
            expect(order[2]).toBe('task3');
        });
    });

    describe('YAML Integration', () => {
        test('should load from YAML file correctly', async () => {
            const yamlPath = path.join(__dirname, 'fixtures', 'test-tasks.yaml');
            await dag.loadFromYaml(yamlPath);
            
            expect(dag.hasNode('TASK-1')).toBe(true);
            expect(dag.hasNode('TASK-2')).toBe(true);
            expect(dag.hasEdge('TASK-1', 'TASK-2')).toBe(true);
        });

        test('should handle invalid YAML files', async () => {
            const yamlPath = path.join(__dirname, 'fixtures', 'invalid-tasks.yaml');
            await expect(dag.loadFromYaml(yamlPath)).rejects.toThrow();
        });
    });

    describe('Error Handling', () => {
        test('should handle missing nodes in edge creation', () => {
            expect(() => dag.addEdge('nonexistent1', 'nonexistent2'))
                .toThrow('Node does not exist');
        });

        test('should handle invalid node data', () => {
            expect(() => dag.addNode('task1', null))
                .toThrow('Invalid node data');
        });
    });
});
