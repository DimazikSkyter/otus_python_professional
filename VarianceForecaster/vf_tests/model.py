import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pytest
from vf_app.model.model import Model


@pytest.fixture(scope="module")
def poly_model():
    size = 150
    x = np.arange(-size, size, dtype=float)
    # rng = np.random.RandomState(0)
    # coeffs = rng.randn(4) * 100
    # print(f"Training coeffs are {coeffs}")
    poly = np.poly1d([0.0000013, -0.00010, -0.015, 0.95, -9, 0])
    y = poly(x)
    deriv = poly.deriv()
    roots = deriv.r
    true_bps = np.array(
        sorted(
            [
                int(np.round(r.real))
                for r in roots
                if np.isreal(r) and -size <= r.real < size
            ]
        ),
        dtype=int,
    )
    y_labels = np.zeros(2 * size, dtype=np.int64)
    y_labels[true_bps + size] = 1
    print("Derivative roots:", roots)
    print("indexes of y_labels:", np.where(y_labels == 1)[0])
    X = x.reshape(-1, 1)
    model = Model(z_score_percentile=75)
    model.train_z_score(X, y_labels)
    model.calc_break_points(X)
    return model, x, y, true_bps


def test_predict_single_seria_identity(poly_model):
    model, x, y, true_bps = poly_model
    y_hat = model.predict_single_seria(x, y)
    assert isinstance(y_hat, np.ndarray)
    assert y_hat.shape == y.shape
    #    assert np.allclose(y_hat, y, rtol=1e-6)
    pred_bps = model.break_points
    #    assert set(pred_bps.tolist()) == set(true_bps.tolist())
    plt.figure()
    plt.plot(x, y, label="True poly")
    plt.plot(x, y_hat, "--", label="PWLF fit")
    # for bp in true_bps:
    #     plt.axvline(bp, color='red', linestyle=':', alpha=0.6)
    # for bp in pred_bps:
    #     plt.axvline(x[bp], color='blue', linestyle='--', alpha=0.6)
    plt.title("Polynomial Degree 5 Single Series")
    plt.legend()
    plt.show()


def make_global_seria(
    x_series_list: "list[npt.NDArray[np.float64]]", y: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    # ������ ������ (m+1, n) ��� m ����� x � ��������� ������ y
    all_rows = list(x_series_list) + [y]
    return np.vstack(all_rows)


def test_predict_full_seria_two_x_series():
    # ���������� �������: ��� ���������� X � ���� Y
    size = 10000
    x1 = np.arange(size, dtype=float)
    x2 = np.arange(20000, 20000 + size, dtype=float)
    y = np.arange(size, dtype=float)

    global_seria = make_global_seria([x1, x2], y)

    model = Model()

    # Monkey-patch calc_break_points, ����� �� �������� �� RFC
    def fake_calc(X):
        # ���� ������� ����� �� Y
        model.break_points = np.array([y[0], y[-1]], dtype=np.float64)

    model.calc_break_points = fake_calc

    results = model.predict_full_seria(global_seria)
    # ������� 2 ��������, �� ������ �� ������ x-�����
    assert isinstance(results, list)
    assert len(results) == 2
    # ������ ������� ����� y
    assert np.allclose(results[0], y)
    assert np.allclose(results[1], y)


if __name__ == "__main__":
    pytest.main()
