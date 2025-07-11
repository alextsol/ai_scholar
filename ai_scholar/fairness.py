import numpy as np
from fairlearn.metrics import MetricFrame

def compute_fairness_metrics(papers):
    valid_papers = [paper for paper in papers if isinstance(paper, dict)]
    if not valid_papers:
        return {}
    
    scores = [paper.get("score", 1.0) for paper in valid_papers]
    groups = [paper.get("source", "unknown") for paper in valid_papers]
    dummy_labels = np.zeros(len(scores))
    
    mf = MetricFrame(
        metrics=lambda y_true, y_pred: np.mean(y_pred),
        y_true=dummy_labels,
        y_pred=scores,
        sensitive_features=groups
    )
    
    return mf.by_group.to_dict()
