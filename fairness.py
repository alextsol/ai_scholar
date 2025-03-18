import numpy as np
from fairlearn.metrics import MetricFrame

def compute_fairness_metrics(papers):
    valid_papers = [paper for paper in papers if isinstance(paper, dict)]
    if not valid_papers:
        return {}
    
    # Assign a dummy score of 1.0 for each paper (or replace with a real quality metric)
    scores = [paper.get("score", 1.0) for paper in valid_papers]
    # Use the 'source' as the sensitive feature, defaulting to "unknown"
    groups = [paper.get("source", "unknown") for paper in valid_papers]
    
    # Create dummy true labels since we don't have actual ones
    dummy_labels = np.zeros(len(scores))
    
    mf = MetricFrame(
        metrics=lambda y_true, y_pred: np.mean(y_pred),
        y_true=dummy_labels,
        y_pred=scores,
        sensitive_features=groups
    )
    
    # Convert the resulting Series to a dictionary to avoid ambiguity in truth value.
    return mf.by_group.to_dict()
