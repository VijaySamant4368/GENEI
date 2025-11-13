# %%
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from lifelines import KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test
from lifelines.utils import concordance_index
import matplotlib.pyplot as plt

# We’ll use the same feature set you used to compute risk_score
FEATURES = parameters + ["Cyto"]

# Use the labeled dataframe with risk_score and risk_group
df = train_labeled.copy()

# --- 1) Train/Test split (80/20), stratified on combined OS/EFS event flags ---
stratify_key = df[OS_EVENT_COL].astype(str) + "_" + df[EFS_EVENT_COL].astype(str)

X = df[FEATURES].to_numpy()
y_true_groups = df["risk_group"]  # original GENEI-1..3 from your KMeans+median mapping

X_train, X_test, y_true_train, y_true_test, train_idx, test_idx = train_test_split(
    X, y_true_groups, df.index, test_size=0.2, random_state=SEED, stratify=stratify_key
)

# Helpers for survival data splits
def split_surv(colname):
    return df.loc[train_idx, colname].to_numpy(), df.loc[test_idx, colname].to_numpy()

OS_time_tr, OS_time_te = split_surv(OS_TIME_COL)
OS_event_tr, OS_event_te = split_surv(OS_EVENT_COL)
EFS_time_tr, EFS_time_te = split_surv(EFS_TIME_COL)
EFS_event_tr, EFS_event_te = split_surv(EFS_EVENT_COL)

# --- 2) KNN to generate labels on TRAIN ---
# Train KNN on TRAIN features to predict your existing risk_group (GENEI-1..3)
knn = KNeighborsClassifier(n_neighbors=7, weights="distance", metric="minkowski")
knn.fit(X_train, y_true_train)

# KNN "classes" (labels) on TRAIN — these will supervise the Decision Tree
y_knn_train = knn.predict(X_train)

# --- 3) Decision Tree (labeled by KNN classes) and predict TEST classes ---
dt = DecisionTreeClassifier(
    random_state=SEED,
    max_depth=4,              # modest regularization; tweak if needed
    min_samples_leaf=10
)
dt.fit(X_train, y_knn_train)

# Final classes for TEST set (from Decision Tree)
y_dt_test = dt.predict(X_test)

# --- 4) KM curves + Logrank + C-index for OS and EFS ---
def ordered_numeric_risk(labels, rank_map):
    """
    Map GENEI-1..3 to ascending numeric risk (1 < 2 < 3) using the TRAIN order you built earlier.
    """
    # rank_map already maps raw cluster ids to GENEI-1..k; build inverse numeric map:
    # Ensure GENEI-X -> X as integer
    to_num = labels.map(lambda s: int(s.split("-")[1]))
    return to_num.to_numpy()

def km_compare_and_cindex(time_test, event_test, groups_test, title_prefix):
    """
    Draw KM curves for each predicted group, compute multivariate logrank p, and C-index.
    """
    # Ensure pandas Series for consistent indexing
    import pandas as _pd
    if not isinstance(groups_test, _pd.Series):
        groups_test = _pd.Series(groups_test, index=test_idx, name="group")

    # Numeric risk score for C-index (higher number = higher risk)
    risk_numeric = ordered_numeric_risk(groups_test, rank_map)

    # KM curves
    kmf = KaplanMeierFitter()
    plt.figure(figsize=(7,5))
    for grp in sorted(groups_test.unique(), key=lambda s: int(s.split("-")[1])):  # order GENEI-1..k
        mask = (groups_test == grp).to_numpy()
        kmf.fit(time_test[mask], event_observed=event_test[mask], label=grp)
        kmf.plot(ci_show=False)
    plt.title(f"{title_prefix} — Kaplan–Meier by Decision-Tree Predicted Groups")
    plt.xlabel("Time")
    plt.ylabel("Survival probability")
    plt.grid(True, alpha=0.3)
    plt.show()

    # Logrank test across multiple groups
    lr = multivariate_logrank_test(
        event_durations=time_test,
        groups=groups_test,
        event_observed=event_test
    )
    pval = float(lr.p_value)

    # C-index (use negative risk if larger number => higher risk)
    cval = concordance_index(time_test, -risk_numeric, event_test)

    print(f"{title_prefix}: logrank p-value = {pval:.3e} | C-index = {cval:.3f}")

# Build Series for groups aligned to test_idx
y_dt_test_s = y_true_test.copy()
y_dt_test_s[:] = y_dt_test

# OS
km_compare_and_cindex(OS_time_te, OS_event_te, y_dt_test_s, "OS")

# EFS
km_compare_and_cindex(EFS_time_te, EFS_event_te, y_dt_test_s, "EFS")

# --- 5) (Optional) also show KNN vs DT on TEST side-by-side KM/C for quick comparison ---
# If you’d like to compare KNN and Decision Tree curves/C-values:
y_knn_test = knn.predict(X_test)
y_knn_test_s = y_true_test.copy()
y_knn_test_s[:] = y_knn_test

print("\n=== KNN (direct) on TEST ===")
km_compare_and_cindex(OS_time_te, OS_event_te, y_knn_test_s, "OS (KNN)")
km_compare_and_cindex(EFS_time_te, EFS_event_te, y_knn_test_s, "EFS (KNN)")

print("\n=== Decision Tree (trained on KNN labels) on TEST ===")
km_compare_and_cindex(OS_time_te, OS_event_te, y_dt_test_s, "OS (DT)")
km_compare_and_cindex(EFS_time_te, EFS_event_te, y_dt_test_s, "EFS (DT)")
