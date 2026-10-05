#!/usr/bin/env python3
"""
IrrigaSense — First-Order Takagi-Sugeno ANFIS Implementation (Milestone 8B)
===========================================================================
Transparent, inspectable, vectorized Adaptive Neuro-Fuzzy Inference System.

Topology:
  - Layer 1: Gaussian Membership Functions (premise parameters: c, sigma)
  - Layer 2: Product T-norm Rule Firing Strengths (log-domain stability)
  - Layer 3: Normalized Rule Firing Strengths (softmax / log-sum-exp)
  - Layer 4: First-Order Sugeno Consequents (linear: p1*x1 + ... + p5*x5 + r)
  - Layer 5: Weighted Output Summation

Hybrid Learning:
  - Consequents: Regularized Least Squares Estimation (LSE / Ridge SVD)
  - Premises: Error Backpropagation with Adam Optimizer
"""

import itertools
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


class ANFISModel:
    """
    First-Order Takagi-Sugeno Adaptive Neuro-Fuzzy Inference System.
    """

    def __init__(
        self,
        n_inputs: int = 5,
        n_mfs_per_input: int = 2,
        feature_names: Optional[List[str]] = None,
        target_name: str = "target_mean_24h",
        model_name: str = "ANFIS_Architecture_A",
    ):
        self.n_inputs = n_inputs
        self.n_mfs = n_mfs_per_input
        self.n_rules = n_mfs_per_input ** n_inputs
        self.target_name = target_name
        self.model_name = model_name

        self.feature_names = feature_names or [f"x{i+1}" for i in range(n_inputs)]
        assert len(self.feature_names) == n_inputs, "Feature names length mismatch!"

        # Linguistic labels
        if self.n_mfs == 2:
            self.mf_labels = ["Low", "High"]
        elif self.n_mfs == 3:
            self.mf_labels = ["Low", "Medium", "High"]
        else:
            self.mf_labels = [f"MF_{i+1}" for i in range(self.n_mfs)]

        # Permutations of MF indices for each rule: shape (n_rules, n_inputs)
        # E.g. for M=2: [[0,0,0,0,0], [0,0,0,0,1], ..., [1,1,1,1,1]]
        self.rule_table = np.array(
            list(itertools.product(range(self.n_mfs), repeat=self.n_inputs)),
            dtype=np.int32,
        )

        # Premise parameters:
        # centers c: shape (n_inputs, n_mfs)
        # widths sigma: shape (n_inputs, n_mfs)
        self.c = np.zeros((self.n_inputs, self.n_mfs), dtype=np.float64)
        self.sigma = np.ones((self.n_inputs, self.n_mfs), dtype=np.float64)

        # Consequent parameters: shape (n_rules, n_inputs + 1)
        # Each row has [p1, p2, ..., pn, r]
        self.consequents = np.zeros((self.n_rules, self.n_inputs + 1), dtype=np.float64)

        # Training history & metadata
        self.training_config: Dict[str, Any] = {}
        self.best_epoch: Optional[int] = None
        self.best_val_metrics: Dict[str, float] = {}

    @property
    def total_premise_params(self) -> int:
        return self.n_inputs * self.n_mfs * 2

    @property
    def total_consequent_params(self) -> int:
        return self.n_rules * (self.n_inputs + 1)

    @property
    def total_params(self) -> int:
        return self.total_premise_params + self.total_consequent_params

    @property
    def centers(self) -> np.ndarray:
        return self.c

    @property
    def sigmas(self) -> np.ndarray:
        return self.sigma

    def initialize_premises_from_data(self, X_train_norm: np.ndarray, strategy: str = "quantile") -> None:
        """
        Deterministic, data-driven initialization fitted ONLY on training data.
        Operates on normalized inputs X in [0.0, 1.0].
        Strategies:
          - 'quantile': Centers at training distribution quantiles (Q25/Q75 or Q16.7/Q50/Q83.3).
          - 'evenly_spaced': Centers placed uniformly across the training range [0.0, 1.0].
        """
        assert X_train_norm.shape[1] == self.n_inputs, "Input dimension mismatch!"
        sqrt_2_ln_2 = np.sqrt(2.0 * np.log(2.0))  # approx 1.1774

        for j in range(self.n_inputs):
            col_data = X_train_norm[:, j]
            if strategy == "evenly_spaced":
                if self.n_mfs == 2:
                    c_low, c_high = 0.25, 0.75
                    sigma_val = (c_high - c_low) / (2.0 * sqrt_2_ln_2)
                    self.c[j, 0] = c_low
                    self.c[j, 1] = c_high
                    self.sigma[j, 0] = sigma_val
                    self.sigma[j, 1] = sigma_val
                elif self.n_mfs == 3:
                    c_low, c_med, c_high = 0.1667, 0.50, 0.8333
                    sigma_val = (c_high - c_low) / (4.0 * sqrt_2_ln_2)
                    self.c[j, 0] = c_low
                    self.c[j, 1] = c_med
                    self.c[j, 2] = c_high
                    self.sigma[j, 0] = sigma_val
                    self.sigma[j, 1] = sigma_val
                    self.sigma[j, 2] = sigma_val
                else:
                    centers = np.linspace(0.1, 0.9, self.n_mfs)
                    for m in range(self.n_mfs):
                        self.c[j, m] = centers[m]
                        self.sigma[j, m] = 0.25
            else:  # 'quantile'
                if self.n_mfs == 2:
                    # 2 MFs: Low (Q25), High (Q75)
                    c_low = float(np.percentile(col_data, 25))
                    c_high = float(np.percentile(col_data, 75))
                    if abs(c_high - c_low) < 1e-4:
                        c_low, c_high = 0.25, 0.75
                    sigma_val = max(0.05, (c_high - c_low) / (2.0 * sqrt_2_ln_2))
                    self.c[j, 0] = c_low
                    self.c[j, 1] = c_high
                    self.sigma[j, 0] = sigma_val
                    self.sigma[j, 1] = sigma_val
                elif self.n_mfs == 3:
                    # 3 MFs: Low (Q16.7), Medium (Q50), High (Q83.3)
                    c_low = float(np.percentile(col_data, 16.67))
                    c_med = float(np.percentile(col_data, 50.0))
                    c_high = float(np.percentile(col_data, 83.33))
                    if abs(c_high - c_low) < 1e-4:
                        c_low, c_med, c_high = 0.2, 0.5, 0.8
                    sigma_val = max(0.05, (c_high - c_low) / (4.0 * sqrt_2_ln_2))
                    self.c[j, 0] = c_low
                    self.c[j, 1] = c_med
                    self.c[j, 2] = c_high
                    self.sigma[j, 0] = sigma_val
                    self.sigma[j, 1] = sigma_val
                    self.sigma[j, 2] = sigma_val
                else:
                    quantiles = np.linspace(10, 90, self.n_mfs)
                    for m, q in enumerate(quantiles):
                        self.c[j, m] = float(np.percentile(col_data, q))
                        self.sigma[j, m] = 0.25

    def compute_memberships(self, X: np.ndarray) -> np.ndarray:
        """
        Layer 1: Computes Gaussian membership grades for each input.
        Returns: mu of shape (S, n_inputs, n_mfs)
        """
        S = X.shape[0]
        # X: (S, N, 1), c: (1, N, M), sigma: (1, N, M)
        X_exp = X[:, :, np.newaxis]
        c_exp = self.c[np.newaxis, :, :]
        sig_exp = np.maximum(1e-4, self.sigma[np.newaxis, :, :])
        diff = X_exp - c_exp
        mu = np.exp(-0.5 * (diff / sig_exp) ** 2)
        return mu

    def compute_firing_strengths(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Layer 2 & 3: Computes rule firing strengths and normalized firing strengths.
        Uses log-space formulation for numerical stability:
          z_i = - sum_j [ (x_j - c_{j, m_i})^2 / (2 * sigma_{j, m_i}^2) ]
          w_bar_i = softmax(z)_i
        Returns:
          z: log firing strengths (S, n_rules)
          w_bar: normalized firing strengths (S, n_rules), sum over axis 1 = 1.0
        """
        S = X.shape[0]
        z = np.zeros((S, self.n_rules), dtype=np.float64)

        for j in range(self.n_inputs):
            m_idx = self.rule_table[:, j]  # (n_rules,)
            c_j = self.c[j, m_idx]  # (n_rules,)
            sig_j = np.maximum(1e-4, self.sigma[j, m_idx])  # (n_rules,)
            diff = X[:, j:j+1] - c_j[np.newaxis, :]  # (S, n_rules)
            z -= (diff ** 2) / (2.0 * (sig_j ** 2))

        # Softmax in log-space (log-sum-exp trick)
        z_max = np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(z - z_max)
        sum_exp = np.sum(exp_z, axis=1, keepdims=True)
        sum_exp = np.maximum(1e-12, sum_exp)
        w_bar = exp_z / sum_exp
        return z, w_bar

    def build_consequent_design_matrix(
        self, X: np.ndarray, w_bar: np.ndarray
    ) -> np.ndarray:
        """
        Layer 4 & 5 design matrix constructor:
        For sample s, A[s] = [w_bar[s,0]*X_aug[s], w_bar[s,1]*X_aug[s], ...]
        Shape: (S, n_rules * (n_inputs + 1))
        """
        S = X.shape[0]
        K = self.n_inputs + 1
        X_aug = np.hstack([X, np.ones((S, 1), dtype=np.float64)])  # (S, K)

        # Vectorized outer product: (S, n_rules, 1) * (S, 1, K) -> (S, n_rules, K)
        A_3d = w_bar[:, :, np.newaxis] * X_aug[:, np.newaxis, :]
        A = A_3d.reshape(S, self.n_rules * K)
        return A

    def fit_consequents_lse(
        self, X: np.ndarray, y: np.ndarray, reg: float = 1e-4
    ) -> np.ndarray:
        """
        Solves for optimal linear consequent parameters using Ridge Least Squares Estimation:
          P = (A^T A + lambda * I)^(-1) A^T y
        """
        _, w_bar = self.compute_firing_strengths(X)
        A = self.build_consequent_design_matrix(X, w_bar)

        n_params = A.shape[1]
        ATA = A.T @ A + reg * np.eye(n_params, dtype=np.float64)
        ATy = A.T @ y

        # Solve system
        P_flat = np.linalg.solve(ATA, ATy)
        self.consequents = P_flat.reshape(self.n_rules, self.n_inputs + 1)
        return self.consequents

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Performs full forward inference:
          Layer 1 -> Layer 2 -> Layer 3 -> Layer 4 -> Layer 5
        Returns continuous scalar predictions y_pred of shape (S,).
        """
        _, w_bar = self.compute_firing_strengths(X)
        S = X.shape[0]
        K = self.n_inputs + 1
        X_aug = np.hstack([X, np.ones((S, 1), dtype=np.float64)])  # (S, K)

        # Rule consequent values f_i(X) = X_aug @ P_i
        # consequents: (n_rules, K), X_aug: (S, K)
        # f_all: (S, n_rules)
        f_all = X_aug @ self.consequents.T
        y_pred = np.sum(w_bar * f_all, axis=1)
        return y_pred

    def compute_premise_gradients(
        self, X: np.ndarray, y: np.ndarray, y_pred: np.ndarray, w_bar: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Layer 5 backpropagation to Layer 1 premise parameters.
        Computes analytical gradients dE/dc and dE/dsigma for MSE loss:
          E = 0.5 * mean( (y_pred - y)^2 )
        """
        S = X.shape[0]
        K = self.n_inputs + 1
        e = (y_pred - y)  # (S,)

        X_aug = np.hstack([X, np.ones((S, 1), dtype=np.float64)])
        f_all = X_aug @ self.consequents.T  # (S, n_rules)

        # Softmax derivative: delta_{s, i} = (1/S) * e_s * w_bar_{s, i} * (f_{s, i} - y_pred_s)
        delta = (1.0 / S) * e[:, np.newaxis] * w_bar * (f_all - y_pred[:, np.newaxis])

        grad_c = np.zeros_like(self.c)
        grad_sigma = np.zeros_like(self.sigma)

        for j in range(self.n_inputs):
            for m in range(self.n_mfs):
                rules_with_m = np.where(self.rule_table[:, j] == m)[0]
                Delta = np.sum(delta[:, rules_with_m], axis=1)  # (S,)
                diff = X[:, j] - self.c[j, m]
                sig = max(1e-4, self.sigma[j, m])
                grad_c[j, m] = np.sum(Delta * diff) / (sig ** 2)
                grad_sigma[j, m] = np.sum(Delta * (diff ** 2)) / (sig ** 3)

        return grad_c, grad_sigma

    def to_dict(self) -> Dict[str, Any]:
        """Serializes complete model state to a JSON-compatible dictionary."""
        rules_list = []
        for i in range(self.n_rules):
            antecedents = {
                self.feature_names[j]: self.mf_labels[self.rule_table[i, j]]
                for j in range(self.n_inputs)
            }
            consequent_coeffs = {
                self.feature_names[j]: round(float(self.consequents[i, j]), 6)
                for j in range(self.n_inputs)
            }
            consequent_coeffs["intercept"] = round(float(self.consequents[i, self.n_inputs]), 6)
            rules_list.append({
                "rule_id": i + 1,
                "antecedents": antecedents,
                "consequent": consequent_coeffs,
            })

        premise_dict = {}
        for j, feat in enumerate(self.feature_names):
            premise_dict[feat] = {
                self.mf_labels[m]: {
                    "center": round(float(self.c[j, m]), 6),
                    "sigma": round(float(self.sigma[j, m]), 6),
                }
                for m in range(self.n_mfs)
            }

        return {
            "model_metadata": {
                "model_name": self.model_name,
                "algorithm": "First-Order Takagi-Sugeno ANFIS",
                "n_inputs": self.n_inputs,
                "n_mfs_per_input": self.n_mfs,
                "n_rules": self.n_rules,
                "total_premise_params": self.total_premise_params,
                "total_consequent_params": self.total_consequent_params,
                "total_params": self.total_params,
                "feature_names": self.feature_names,
                "target_name": self.target_name,
                "best_epoch": self.best_epoch,
                "best_val_metrics": self.best_val_metrics,
                "training_config": self.training_config,
            },
            "premise_parameters": premise_dict,
            "rules": rules_list,
        }

    def save_model(self, file_path: Union[str, Path]) -> None:
        """Saves model to a JSON artifact file."""
        state = self.to_dict()
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(state, f, indent=2)

    @classmethod
    def load_model(cls, file_path: Union[str, Path]) -> "ANFISModel":
        """Loads model from a JSON artifact file."""
        with open(file_path, "r") as f:
            state = json.load(f)
        meta = state["model_metadata"]
        model = cls(
            n_inputs=meta["n_inputs"],
            n_mfs_per_input=meta["n_mfs_per_input"],
            feature_names=meta["feature_names"],
            target_name=meta["target_name"],
            model_name=meta["model_name"],
        )
        model.best_epoch = meta.get("best_epoch")
        model.best_val_metrics = meta.get("best_val_metrics", {})
        model.training_config = meta.get("training_config", {})

        # Load premises
        for j, feat in enumerate(model.feature_names):
            feat_dict = state["premise_parameters"][feat]
            for m, label in enumerate(model.mf_labels):
                model.c[j, m] = feat_dict[label]["center"]
                model.sigma[j, m] = feat_dict[label]["sigma"]

        # Load consequents
        for i, rule in enumerate(state["rules"]):
            for j, feat in enumerate(model.feature_names):
                model.consequents[i, j] = rule["consequent"][feat]
            model.consequents[i, model.n_inputs] = rule["consequent"]["intercept"]

        return model
