const { DAG } = require('./dag');
const path = require('path');
const fs = require('fs');

jest.mock('fs');

describe('DAG', () => {
    let dag;

    beforeEach(() => {
        dag = new DAG();
        jest.clearAllMocks();
    });

    test('should create empty graph', () => {
        expect(dag.getAllNodes()).toHaveLength(0);
    });

    test('should add nodes', () => {
        dag.addNode(1);
        dag.addNode(2);
        expect(dag.nodes.has(1)).toBe(true);
        expect(dag.nodes.has(2)).toBe(true);
    });

    test('should prevent duplicate nodes', () => {
        dag.addNode(1);
        expect(() => dag.addNode(1)).toThrow();
    });

    test('should add edges', () => {
        dag.addNode(1);
        dag.addNode(2);
        dag.addEdge(1, 2);
        expect(dag.edges.get(1)).toContain(2);
    });

    test('should detect cycles', () => {
        dag.addNode(1);
        dag.addNode(2);
        dag.addNode(3);
        dag.addEdge(1, 2);
        dag.addEdge(2, 3);
        dag.addEdge(3, 1);
        expect(dag.hasCycle()).toBe(true);
    });

    test('should not detect cycles in acyclic graph', () => {
        dag.addNode(1);
        dag.addNode(2);
        dag.addNode(3);
        dag.addEdge(1, 2);
        dag.addEdge(2, 3);
        expect(dag.hasCycle()).toBe(false);
    });

    test('should get roots', () => {
        dag.addNode(1);
        dag.addNode(2);
        dag.addNode(3);
        dag.addEdge(1, 2);
        dag.addEdge(2, 3);
        expect(Array.from(dag.getRoots())).toEqual([1]);
    });

    test('should get leaves', () => {
        dag.addNode(1);
        dag.addNode(2);
        dag.addNode(3);
        dag.addEdge(1, 2);
        dag.addEdge(2, 3);
        expect(Array.from(dag.getLeaves())).toEqual([3]);
    });

    test('should load from YAML', () => {
        const mockYaml = `
next_available_tasks:
  - id: 1
    name: Task 1
    description: First task
    blocking: [2, 3]
    blocked_by: []

  - id: 2
    name: Task 2
    description: Second task
    blocking: [4]
    blocked_by: [1]

  - id: 3
    name: Task 3
    description: Third task
    blocking: [4]
    blocked_by: [1]

  - id: 4
    name: Task 4
    description: Fourth task
    blocking: []
    blocked_by: [2, 3]
`;

        const yamlPath = path.join(__dirname, 'test.yaml');
        fs.readFileSync.mockReturnValue(mockYaml);

        const dag = DAG.fromYaml(yamlPath);
        expect(dag.nodes.has(1)).toBe(true);
        expect(dag.nodes.has(2)).toBe(true);
        expect(dag.nodes.has(3)).toBe(true);
        expect(dag.nodes.has(4)).toBe(true);
        expect(Array.from(dag.edges.get(1))).toEqual(expect.arrayContaining([2, 3]));
        expect(Array.from(dag.edges.get(2))).toEqual(expect.arrayContaining([4]));
        expect(Array.from(dag.edges.get(3))).toEqual(expect.arrayContaining([4]));
    });
});
