"""
Knowledge Graph Module — Neo4j Integration for JEBAT
Q4 2026: Knowledge Graph implementation

Provides graph-based relationship queries for memory, agents, and skills.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    id: str
    label: str  # memory, agent, skill, user, session, concept
    properties: dict = field(default_factory=dict)


@dataclass
class GraphRelationship:
    """Represents a relationship between two nodes."""
    source: str
    target: str
    type: str  # relates_to, triggers, depends_on, learned_from, used_by
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


class KnowledgeGraph:
    """
    Graph-based knowledge representation for JEBAT.
    
    Uses Neo4j for persistent storage when available,
    falls back to in-memory graph for development.
    
    Supports:
    - Memory relationship mapping
    - Agent-skill affinity tracking
    - Concept clustering
    - Query by relationship type
    - Graph traversal for context expansion
    """
    
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        self._nodes: dict[str, GraphNode] = {}
        self._relationships: list[GraphRelationship] = []
        self._neo4j_driver = None
        
        if uri and username and password:
            self._init_neo4j(uri, username, password)
    
    def _init_neo4j(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection."""
        try:
            from neo4j import GraphDatabase
            self._neo4j_driver = GraphDatabase.driver(uri, auth=(username, password))
            # Verify connection
            with self._neo4j_driver.session() as session:
                session.run("RETURN 1")
        except ImportError:
            pass  # Neo4j not installed, use in-memory
        except Exception:
            pass  # Connection failed, use in-memory
    
    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        self._nodes[node.id] = node
        if self._neo4j_driver:
            with self._neo4j_driver.session() as session:
                session.run(
                    "MERGE (n:Node {id: $id, label: $label, properties: $props})",
                    id=node.id, label=node.label, props=node.properties
                )
    
    def add_relationship(self, rel: GraphRelationship):
        """Add a relationship between two nodes."""
        self._relationships.append(rel)
        if self._neo4j_driver:
            with self._neo4j_driver.session() as session:
                session.run(
                    "MATCH (a:Node {id: $source}), (b:Node {id: $target}) "
                    "MERGE (a)-[r:REL {type: $type, weight: $weight}]->(b)",
                    source=rel.source, target=rel.target,
                    type=rel.type, weight=rel.weight
                )
    
    def find_related(self, node_id: str, relationship_type: str = None, max_depth: int = 2) -> list[GraphNode]:
        """Find nodes related to a given node."""
        if self._neo4j_driver:
            return self._find_related_neo4j(node_id, relationship_type, max_depth)
        return self._find_related_memory(node_id, relationship_type, max_depth)
    
    def _find_related_neo4j(self, node_id: str, relationship_type: str, max_depth: int) -> list[GraphNode]:
        """Query Neo4j for related nodes."""
        with self._neo4j_driver.session() as session:
            query = """
            MATCH path = (start:Node {id: $id})-[:REL*1..$depth]-(related:Node)
            WHERE $type IS NULL OR ANY(r IN relationships(path) WHERE r.type = $type)
            RETURN DISTINCT related
            """
            result = session.run(query, id=node_id, type=relationship_type, depth=max_depth)
            return [GraphNode(id=r["related"]["id"], label=r["related"]["label"], properties=r["related"]["properties"]) for r in result]
    
    def _find_related_memory(self, node_id: str, relationship_type: str, max_depth: int) -> list[GraphNode]:
        """In-memory graph traversal."""
        if node_id not in self._nodes:
            return []
        
        visited = {node_id}
        queue = [(node_id, 0)]
        results = []
        
        while queue:
            current_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            
            for rel in self._relationships:
                if rel.type == relationship_type or relationship_type is None:
                    neighbor_id = None
                    if rel.source == current_id:
                        neighbor_id = rel.target
                    elif rel.target == current_id:
                        neighbor_id = rel.source
                    
                    if neighbor_id and neighbor_id not in visited:
                        visited.add(neighbor_id)
                        if neighbor_id in self._nodes:
                            results.append(self._nodes[neighbor_id])
                        queue.append((neighbor_id, depth + 1))
        
        return results
    
    def get_clusters(self, min_size: int = 3) -> list[list[str]]:
        """Find clusters of related nodes."""
        # Simple connected components algorithm
        visited = set()
        clusters = []
        
        for node_id in self._nodes:
            if node_id not in visited:
                cluster = []
                queue = [node_id]
                while queue:
                    current = queue.pop(0)
                    if current in visited:
                        continue
                    visited.add(current)
                    cluster.append(current)
                    
                    for rel in self._relationships:
                        if rel.source == current and rel.target not in visited:
                            queue.append(rel.target)
                        elif rel.target == current and rel.source not in visited:
                            queue.append(rel.source)
                
                if len(cluster) >= min_size:
                    clusters.append(cluster)
        
        return clusters
    
    def get_stats(self) -> dict:
        """Get graph statistics."""
        return {
            "nodes": len(self._nodes),
            "relationships": len(self._relationships),
            "node_types": {},
            "relationship_types": {},
        }


# ─── Pre-built graph patterns for JEBAT ────────────────────────────────────────

def build_memory_graph(memory_items: list[dict]) -> KnowledgeGraph:
    """Build a knowledge graph from memory items."""
    graph = KnowledgeGraph()
    
    for item in memory_items:
        node = GraphNode(
            id=item.get("id", f"mem_{hash(item.get('content', ''))}"),
            label="memory",
            properties={
                "content": item.get("content", ""),
                "layer": item.get("layer", "m1"),
                "heat": item.get("heat", 0),
                "tags": item.get("tags", []),
            }
        )
        graph.add_node(node)
    
    # Create relationships based on shared tags
    for i, item1 in enumerate(memory_items):
        for item2 in memory_items[i+1:]:
            shared_tags = set(item1.get("tags", [])) & set(item2.get("tags", []))
            if shared_tags:
                rel = GraphRelationship(
                    source=f"mem_{hash(item1.get('content', ''))}",
                    target=f"mem_{hash(item2.get('content', ''))}",
                    type="relates_to",
                    weight=len(shared_tags) * 0.5,
                    properties={"shared_tags": list(shared_tags)}
                )
                graph.add_relationship(rel)
    
    return graph


def build_skill_graph(skills: list[dict]) -> KnowledgeGraph:
    """Build a knowledge graph from skills."""
    graph = KnowledgeGraph()
    
    for skill in skills:
        node = GraphNode(
            id=skill.get("name", "unknown"),
            label="skill",
            properties={
                "category": skill.get("category", "general"),
                "description": skill.get("description", ""),
            }
        )
        graph.add_node(node)
    
    return graph
