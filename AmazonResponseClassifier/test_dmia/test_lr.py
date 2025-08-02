import numpy as np
import pytest
from dmia.classifiers.logistic_regression import LogisticRegression
from dmia.gradient_check import grad_check_sparse
from dmia.utils import plot_surface
from matplotlib import pyplot as plt
from scipy import sparse
from sklearn.datasets import make_classification


@pytest.fixture(scope="module")
def prepare_batches():
    X, y = make_classification(
        n_samples=100,
        n_features=2,
        n_informative=2,
        n_redundant=0,
        n_classes=2,
        n_clusters_per_class=1,
        random_state=42,
    )

    def sample_batch(batch_size=32):
        indices = np.random.choice(len(X), batch_size, replace=True)
        return X[indices], y[indices]

    return X, y, sample_batch


def test_loss_gradient_correctness(prepare_batches):
    X, y, sample_batch = prepare_batches
    X_batch, y_batch = sample_batch(batch_size=10)

    model = LogisticRegression()
    model.w = np.random.randn(X.shape[1] + 1) * 0.01

    X_bias = model.append_biases(sparse.csr_matrix(X_batch))

    loss, analytic_grad = model.loss(X_bias, y_batch, reg=0.1)

    def loss_func(w):
        model.w = w.copy()
        l, _ = model.loss(X_bias, y_batch, reg=0.1)
        return l

    grad_check_sparse(loss_func, model.w, analytic_grad, num_checks=5)

    print(f"test loss={loss} and analytic_grad={analytic_grad}")

    assert np.isfinite(loss)


def test_plot_surface_learning_works():
    # Простые 2D данные для визуализации
    X, y = make_classification(
        n_samples=1000,
        n_features=2,
        n_informative=2,
        n_redundant=0,
        n_clusters_per_class=1,
        random_state=42,
    )

    X_train, y_train = X[:800], y[:800]
    X_test, y_test = X[800:], y[800:]

    model = LogisticRegression()
    model.train(
        X_train, y_train, num_iters=1000, learning_rate=0.1, batch_size=32, reg=0.01
    )

    y_pred = model.predict(X_test)
    accuracy = np.mean(y_pred == y_test)
    assert accuracy > 0.9, f"Accuracy too low: {accuracy}"

    plot_surface(X_test, y_test, model)
    plt.title(f"Decision boundary (acc={accuracy:.2f})")
    plt.show()
