import numpy as np

def brownian_motion(prices,
                    simulation_paths=1000,
                    n_days=252,
                    dt=1/252,
                    window_size=30):
    returns_pct = prices.tail(window_size).pct_change().dropna()
    current_price = prices.iloc[-1]
    mean = returns_pct.mean() * 252
    std = returns_pct.std() * np.sqrt(252)

    dW = np.random.normal(0, 1, (simulation_paths, n_days))
    drift = (mean - 0.5 * std ** 2) * dt
    diffusion = std * np.sqrt(dt) * dW
    S = current_price * np.exp(np.cumsum(drift + diffusion, axis=1))
    return S