from seqeval.metrics import f1_score, precision_score, recall_score

def test_metrics():
    true_labels = [["B-PER", "I-PER", "O", "B-ORG"]]
    true_predictions = [["B-PER", "I-PER", "O", "B-ORG"]]
    
    print(f"Precision: {precision_score(true_labels, true_predictions)}")
    print(f"Recall: {recall_score(true_labels, true_predictions)}")
    print(f"F1: {f1_score(true_labels, true_predictions)}")

    true_predictions_miss = [["O", "O", "O", "O"]]
    print(f"Miss F1: {f1_score(true_labels, true_predictions_miss)}")

if __name__ == "__main__":
    test_metrics()
