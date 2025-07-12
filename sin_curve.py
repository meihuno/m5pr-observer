
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# パラメータ設定
days = 300  # シミュレーション日数
A = 12.0     # 振幅（初期の上下幅）
B = 12.0     # sinの周期調整
C = 0.000001    # 減衰率
D = 1.0     # 線形上昇の傾き
E = 6000     # 初期価格

# 時間（日）
t = np.arange(days)

start_price = 6000
target_price = 12000
sigma = 0.02  # ボラティリティ（変動率）

# 平均成長率 mu を調整して最終価格を目標に近づける
mu = (np.log(target_price / start_price)) / days  # ログ成長率
# print(mu)

# リターン生成（正規分布）
np.random.seed(42)  # 再現性のため
daily_returns = np.random.normal(loc=mu, scale=sigma, size=days)
# 株価モデル: 減衰するsin波 + 線形成長
price = A * np.sin(B * t) * np.exp(-C * t) + D * t + E
price = price + daily_returns

# 日付生成
start_date = pd.to_datetime("2023-01-01")
dates = pd.date_range(start_date, periods=days)

# データフレームに変換
df = pd.DataFrame({'Date': dates, 'Price': price})

# グラフ描画
plt.figure(figsize=(12, 6))
plt.plot(df['Date'], df['Price'], label="Simulated Stock Price", color='blue')
plt.title("Simulated Stock Price: Volatile Start, Upward Trend")
plt.xlabel("Date")
plt.ylabel("Price")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
