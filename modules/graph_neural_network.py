"""Graph Neural Network for Stock Relations — model inter-stock relationships using graph structures.

Builds a stock relationship graph from correlation, supply-chain, and sector
co-membership data, then propagates signals using message-passing to find
hidden alpha from network effects. Pure Python/NumPy implementation.
"""

import math
from typing import Dict, List, Optional, Set, Tuple


def build_adjacency_from_correlations(
    correlation_matrix: Dict[str, Dict[str, float]],
    threshold: float = 0.5,
) -> Dict[str, List[Tuple[str, float]]]:
    """Build graph adjacency list from a correlation matrix.

    Args:
        correlation_matrix: Dict of {ticker: {ticker: correlation}}.
        threshold: Minimum absolute correlation to create an edge.

    Returns:
        Adjacency list: {ticker: [(neighbor, weight), ...]}.
    """
    adj: Dict[str, List[Tuple[str, float]]] = {}
    for src, neighbors in correlation_matrix.items():
        adj.setdefault(src, [])
        for tgt, corr in neighbors.items():
            if src != tgt and abs(corr) >= threshold:
                adj[src].append((tgt, corr))
    return adj


def build_sector_graph(
    sector_map: Dict[str, str],
    weight: float = 0.3,
) -> Dict[str, List[Tuple[str, float]]]:
    """Build edges between stocks in the same sector.

    Args:
        sector_map: {ticker: sector_name}.
        weight: Edge weight for same-sector connection.

    Returns:
        Adjacency list.
    """
    sectors: Dict[str, List[str]] = {}
    for ticker, sector in sector_map.items():
        sectors.setdefault(sector, []).append(ticker)

    adj: Dict[str, List[Tuple[str, float]]] = {}
    for sector, tickers in sectors.items():
        for i, t1 in enumerate(tickers):
            adj.setdefault(t1, [])
            for t2 in tickers[i + 1:]:
                adj[t1].append((t2, weight))
                adj.setdefault(t2, [])
                adj[t2].append((t1, weight))
    return adj


def merge_graphs(
    *graphs: Dict[str, List[Tuple[str, float]]],
) -> Dict[str, List[Tuple[str, float]]]:
    """Merge multiple adjacency lists, summing edge weights.

    Args:
        *graphs: Variable number of adjacency lists.

    Returns:
        Merged adjacency list with combined weights.
    """
    merged: Dict[str, Dict[str, float]] = {}
    for g in graphs:
        for node, edges in g.items():
            merged.setdefault(node, {})
            for neighbor, w in edges:
                merged[node][neighbor] = merged[node].get(neighbor, 0.0) + w

    return {
        node: [(n, w) for n, w in edges.items()]
        for node, edges in merged.items()
    }


def message_passing(
    adj: Dict[str, List[Tuple[str, float]]],
    node_features: Dict[str, float],
    rounds: int = 2,
    aggregation: str = "weighted_mean",
) -> Dict[str, float]:
    """Propagate signals through graph via message passing.

    Args:
        adj: Adjacency list with weights.
        node_features: Initial feature value per node (e.g., momentum score).
        rounds: Number of message passing rounds.
        aggregation: 'weighted_mean' or 'weighted_sum'.

    Returns:
        Updated node features after propagation.
    """
    features = dict(node_features)

    for _ in range(rounds):
        new_features: Dict[str, float] = {}
        for node in features:
            neighbors = adj.get(node, [])
            if not neighbors:
                new_features[node] = features[node]
                continue

            w_sum = 0.0
            msg_sum = 0.0
            for neighbor, weight in neighbors:
                if neighbor in features:
                    msg_sum += weight * features[neighbor]
                    w_sum += abs(weight)

            if aggregation == "weighted_mean" and w_sum > 0:
                neighbor_agg = msg_sum / w_sum
            else:
                neighbor_agg = msg_sum

            # Combine self with neighbor signal (0.7 self, 0.3 neighbor)
            new_features[node] = 0.7 * features[node] + 0.3 * neighbor_agg

        features = new_features

    return {k: round(v, 6) for k, v in features.items()}


def find_network_alpha(
    adj: Dict[str, List[Tuple[str, float]]],
    node_signals: Dict[str, float],
    rounds: int = 2,
) -> List[Dict]:
    """Find stocks where network effects amplify or contradict individual signals.

    Args:
        adj: Graph adjacency list.
        node_signals: Raw alpha signal per ticker.
        rounds: Message passing rounds.

    Returns:
        List of dicts sorted by network_boost (descending), each with
        ticker, raw_signal, network_signal, network_boost, connected_to.
    """
    propagated = message_passing(adj, node_signals, rounds=rounds)

    results = []
    for ticker in node_signals:
        raw = node_signals[ticker]
        net = propagated.get(ticker, raw)
        boost = net - raw
        neighbors = [n for n, _ in adj.get(ticker, [])]
        results.append({
            "ticker": ticker,
            "raw_signal": round(raw, 4),
            "network_signal": round(net, 4),
            "network_boost": round(boost, 4),
            "connected_to": len(neighbors),
        })

    results.sort(key=lambda x: abs(x["network_boost"]), reverse=True)
    return results


def compute_centrality(adj: Dict[str, List[Tuple[str, float]]]) -> Dict[str, float]:
    """Compute weighted degree centrality for each node.

    Args:
        adj: Graph adjacency list.

    Returns:
        {ticker: centrality_score}.
    """
    centrality: Dict[str, float] = {}
    max_degree = 0.0
    for node, edges in adj.items():
        deg = sum(abs(w) for _, w in edges)
        centrality[node] = deg
        if deg > max_degree:
            max_degree = deg

    if max_degree > 0:
        centrality = {k: round(v / max_degree, 4) for k, v in centrality.items()}

    return centrality
