const { DAG } = require('../dag');
const fs = require('fs');
const yaml = require('js-yaml');

jest.mock('fs');
jest.mock('js-yaml');

describe('DAG', () => {
    test('should create empty graph', () => {
        const dag = new DAG();
        expect(dag.getAllNodes()).toHaveLength(0);
    });

    test('should add nodes', () => {
        const dag = new DAG();
        dag.addNode(1);
        dag.addNode(2);
        expect(dag.getAllNodes()).toHaveLength(2);
    });

    test('should prevent duplicate nodes', () => {
        const dag = new DAG();
        dag.addNode(1);
        expect(() => dag.addNode(1)).toThrow();
    });

    test('should add edges', () => {
        const dag = new DAG();
        dag.addNode(1);
        dag.addNode(2);
        dag.addEdge(1, 2);
        expect(dag.getOutgoingEdges(1)).toContain(2);
    });

    test('should detect cycles', () => {
        const dag = new DAG();
        dag.addNode(1);
        dag.addNode(2);
        dag.addNode(3);
        dag.addEdge(1, 2);
        dag.addEdge(2, 3);
        expect(dag.hasCycle()).toBe(false);
        dag.addEdge(3, 1);
        expect(dag.hasCycle()).toBe(true);
    });

    test('should load from YAML', () => {
        const mockYamlContent = {
            next_available_tasks: [
                {
                    id: 1,
                    title: "Task 1",
                    description: "Description 1",
                    blocking: [2]
                },
                {
                    id: 2,
                    title: "Task 2",
                    description: "Description 2",
                    blocked_by: [1]
                }
            ]
        };

        fs.readFileSync.mockReturnValue('mock yaml content');
        yaml.load.mockReturnValue(mockYamlContent);

        const dag = DAG.fromYaml('test.yaml');
        expect(dag.getAllNodes()).toHaveLength(2);
        expect(dag.getOutgoingEdges(1)).toContain(2);
    });
});
