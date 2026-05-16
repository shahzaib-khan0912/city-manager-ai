
import math
import random
import numpy as np
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.preprocessing import StandardScaler

#risk index mapping
RISK_SCORE = {
    "High":   0.85,
    "Medium": 0.45,
    "Low":    0.10,
}
#feature extraction

def _euclidean(ax, ay, bx, by):
    #euclidean distance
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

def _extract_features(city):
    #extract features matrix
    #gather coordinates of
    industrial_coords = [
        (n.x, n.y) for n in city.nodes.values()
        if n.location_type == "Industrial"
    ]
    hospital_coords = [
        (n.x, n.y) for n in city.nodes.values()
        if n.location_type == "Hospital"
    ]
    powerplant_coords = [
        (n.x, n.y) for n in city.nodes.values()
        if n.location_type == "PowerPlant"
    ]
    #fallback distances when
    MAX_DIST = city.GRID_SIZE * math.sqrt(2)#diagonal across grid

    def nearest_dist(x, y, coord_list):
        if not coord_list:
            return MAX_DIST
        return min(_euclidean(x, y, cx, cy) for cx, cy in coord_list)
    nodes_ordered = list(city.nodes.values())
    rows = []
    for node in nodes_ordered:
        x, y = node.x, node.y
        pop     = float(node.population_density)
        d_ind   = nearest_dist(x, y, industrial_coords)
        d_hosp  = nearest_dist(x, y, hospital_coords)
        d_pp    = nearest_dist(x, y, powerplant_coords)
        is_ind  = 1.0 if node.location_type == "Industrial"  else 0.0
        is_res  = 1.0 if node.location_type == "Residential" else 0.0
        rows.append([pop, d_ind, d_hosp, d_pp, is_ind, is_res])
    X = np.array(rows, dtype=float)
    return nodes_ordered, X
#step 1 k

def _run_kmeans(X_scaled, k_values=(3, 4), random_state=42):
    #fits k means
    best_model  = None
    best_inertia = float('inf')
    best_k      = k_values[0]
    for k in k_values:
        model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        model.fit(X_scaled)
        print(f"K-Means k={k}  inertia={model.inertia_:.2f}")
        if model.inertia_ < best_inertia:
            best_inertia = model.inertia_
            best_model   = model
            best_k       = k
    print(f"Selected k={best_k} (lowest inertia)")
    return best_model.labels_, best_k, best_inertia, best_model
#step 2 synthetic

def _compute_incident_rates(nodes_ordered, X_raw):
    #computes a numeric
    import math
    import random

    MAX_DIST = 15 * math.sqrt(2)
    rates = []
    for i in range(len(nodes_ordered)):
        pop      = X_raw[i, 0]
        d_ind    = X_raw[i, 1]
        d_hosp   = X_raw[i, 2]
        is_ind   = X_raw[i, 4]
        pop_score       = min(pop / 500.0, 1.0)
        ind_proximity   = max(0.0, 1.0 - (d_ind / MAX_DIST))
        ind_bonus       = 1.0 if is_ind == 1.0 else 0.0
        hosp_remoteness = min(d_hosp / MAX_DIST, 1.0)
        rate = (pop_score * 0.40
                + ind_proximity * 0.35
                + ind_bonus * 0.25
                + hosp_remoteness * 0.15)
        noise = random.gauss(0, 0.03)
        rate  = min(1.0, max(0.0, rate + noise))
        rates.append(rate)
    return rates

def _labels_from_rates(incident_rates):
    #converts numeric rates
    labels = []
    for rate in incident_rates:
        if rate > 0.60:
            labels.append("High")
        elif rate > 0.30:
            labels.append("Medium")
        else:
            labels.append("Low")
    return labels

def _assign_crime_labels(nodes_ordered, X_raw, cluster_labels):
    #two step synthetic
    incident_rates = _compute_incident_rates(nodes_ordered, X_raw)
    labels = _labels_from_rates(incident_rates)
    return labels, incident_rates
#step 2 train

def _train_decision_tree(X_scaled, cluster_labels, crime_labels, random_state=42):
    #trains a decision
    #add cluster label
    cluster_col = cluster_labels.reshape(-1, 1).astype(float)
    X_aug = np.hstack([X_scaled, cluster_col])
    feature_names = [
        "pop_density",
        "dist_industrial",
        "dist_hospital",
        "dist_powerplant",
        "is_industrial",
        "is_residential",
        "cluster_id",
    ]
    clf = DecisionTreeClassifier(
        max_depth=5,
        random_state=random_state,
        class_weight="balanced",#handles imbalanced label
    )
    clf.fit(X_aug, crime_labels)
    #print tree for
    tree_text = export_text(clf, feature_names=feature_names)
    print("\nDecision Tree Structure:")
    for line in tree_text.split("\n")[:30]:#print first 30
        print("  " + line)
    if len(tree_text.split("\n")) > 30:
        print("  ... (truncated)")
    #training accuracy
    preds = clf.predict(X_aug)
    accuracy = sum(p == t for p, t in zip(preds, crime_labels)) / len(crime_labels)
    print(f"Training accuracy: {accuracy:.1%}")
    return clf, X_aug, feature_names
#graph integration

def _write_risk_to_graph(city, nodes_ordered, predicted_labels):
    #writes predicted crime
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for node, label in zip(nodes_ordered, predicted_labels):
        coord = (node.x, node.y)
        risk  = RISK_SCORE.get(label, 0.10)
        city.update_risk(coord, risk)
        counts[label] = counts.get(label, 0) + 1
    print(f"\nRisk written to graph:")
    print(f"  High   : {counts['High']:3d} nodes  (risk_index = 0.85, cost multiplier = 1.5x)")
    print(f"  Medium : {counts['Medium']:3d} nodes  (risk_index = 0.45, cost multiplier = 1.2x)")
    print(f"  Low    : {counts['Low']:3d} nodes  (risk_index = 0.10, cost multiplier = 1.0x)")
    return counts

def _deploy_police(city, nodes_ordered, predicted_labels, incident_rates, num_officers=10):
    #allocates 10 police
    ranked = sorted(
        zip(nodes_ordered, predicted_labels, incident_rates),
        key=lambda t: t[2],
        reverse=True
    )
    deployment = []
    zone_counts = {"High": 0, "Medium": 0, "Low": 0}
    for node, label, rate in ranked[:num_officers]:
        deployment.append((node.x, node.y))
        zone_counts[label] = zone_counts.get(label, 0) + 1
    city.police_positions = deployment
    print(f"\nPolice Deployment ({num_officers} officers):")
    print(f"  Officers in High-risk zones  : {zone_counts.get('High', 0)}")
    print(f"  Officers in Medium-risk zones: {zone_counts.get('Medium', 0)}")
    print(f"  Officers in Low-risk zones   : {zone_counts.get('Low', 0)}")
    print(f"  Positions: {deployment}")
    return deployment

def run_crime_risk_pipeline(city):
    #runs the full
    print("\n" + "=" * 50)
    print("  Crime Risk Prediction Pipeline")
    print("=" * 50)
    #step 1 feature
    print("\nStep 1: Extracting features from city graph...")
    nodes_ordered, X_raw = _extract_features(city)
    print(f"Feature matrix: {X_raw.shape[0]} nodes × {X_raw.shape[1]} features")
    #step 2 standardise
    print("\nStep 2: Standardising features (zero mean, unit variance)...")
    scaler  = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    #step 3 k
    print("\nStep 3: K-Means Clustering (testing k=3 and k=4)...")
    cluster_labels, best_k, inertia, kmeans_model = _run_kmeans(X_scaled)
    #step 4 synthetic
    print("\nStep 4: Computing synthetic incident rates per node...")
    crime_labels, incident_rates = _assign_crime_labels(nodes_ordered, X_raw, cluster_labels)
    rate_stats = {
        "min":  min(incident_rates),
        "max":  max(incident_rates),
        "mean": sum(incident_rates) / len(incident_rates)
    }
    print(f"Incident rate stats: "
          f"min={rate_stats['min']:.2f}  max={rate_stats['max']:.2f}  mean={rate_stats['mean']:.2f}")
    label_counts = {l: crime_labels.count(l) for l in ["High", "Medium", "Low"]}
    print(f"Label distribution: {label_counts}")
    #step 5 train
    print("\nStep 5: Training Decision Tree classifier...")
    clf, X_aug, feature_names = _train_decision_tree(
        X_scaled, cluster_labels, crime_labels
    )
    #training accuracy
    preds_train = clf.predict(X_aug)
    accuracy = sum(p == t for p, t in zip(preds_train, crime_labels)) / len(crime_labels)
    #step 6 predict
    print("\nStep 6: Predicting risk levels for all nodes...")
    predicted_labels = list(clf.predict(X_aug))
    #step 7 write
    print("\nStep 7: Writing risk_index to shared city graph...")
    risk_counts = _write_risk_to_graph(city, nodes_ordered, predicted_labels)
    #step 8 police
    print("\nStep 8: Deploying 10 police officers based on risk predictions...")
    police_positions = _deploy_police(
        city, nodes_ordered, predicted_labels, incident_rates, num_officers=10
    )
    #build prediction list
    predictions = [
        ((node.x, node.y), label)
        for node, label in zip(nodes_ordered, predicted_labels)
    ]
    print("\n[OK] Pipeline complete. Edge costs updated system-wide.")
    print("Challenge 3 (GA) and Challenge 4 (A*) will now")
    print("use risk-weighted travel costs automatically.\n")
    return {
        "risk_counts":      risk_counts,
        "best_k":           best_k,
        "kmeans_inertia":   inertia,
        "tree_accuracy":    accuracy,
        "predictions":      predictions,
        "incident_rates":   list(zip([(n.x, n.y) for n in nodes_ordered], incident_rates)),
        "police_positions": police_positions,
    }

def get_risk_summary(city):
    #returns a human
    counts = {"High": 0, "Medium": 0, "Low": 0, "None": 0}
    for node in city.nodes.values():
        if node.risk_index >= 0.7:
            counts["High"] += 1
        elif node.risk_index >= 0.3:
            counts["Medium"] += 1
        elif node.risk_index > 0:
            counts["Low"] += 1
        else:
            counts["None"] += 1
    return counts
