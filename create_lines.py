import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class SimulatedMarket:
    def __init__(self,
                 start_price=6000,
                 end_price=12000,
                 min_price=None,
                 max_price=None,
                 years=15,
                 mu=0.0001,
                 sigma=0.1,
                 trend_type='up',  # 'up', 'down', 'v', 'inverse_v', or 'custom'
                 custom_trend_func=None,
                 jump_day=None, 
                 jump_scale=1.3,
                 random_seed=42):
        
        self.start_price = start_price
        self.end_price = end_price
        self.min_price = min_price or start_price * 0.5
        self.max_price = max_price or end_price * 1.5
        self.years = years
        self.day_num = 252
        self.days = self.day_num * years
        self.mu = mu
        self.sigma = sigma
        self.trend_type = trend_type
        self.custom_trend_func = custom_trend_func
        self.random_seed = random_seed
        self.df = None
        self.jump_day = jump_day
        self.jump_scale = jump_scale
        self.crash_events = []
        # self.set_crash_days()
        # self.set_powerup_days()
        

    def set_crash_days(self):
        # イベント描画
        # --- 暴落イベントを仕込む ---
        day = 0
        for i in range(0, 14):
            day += 500
            if day < self.days:
                self.crash_events.append((day, 0.96))

    def set_powerup_days(self):
        # イベント描画
        # --- 暴落イベントを仕込む ---
        day = 0
        for i in range(0, 1):
            day += 2000
            if day < self.days:
                self.crash_events.append((day, 1.1))


    def generate_with_jump(self):
        base_trend = self._generate_trend()
        log_returns = self._generate_gbm_noise11()

        # 累積リターンを指数化して価格比に変換
        noise_factor = np.exp(np.cumsum(log_returns))
        prices = base_trend * noise_factor

        # --- Jump Event を挿入 ---
        if self.jump_day is not None and 0 < self.jump_day < self.days:
            # 価格を jump_day でスケール
            prices[self.jump_day:] *= self.jump_scale

        # 正規化して終値を目的の終値 or 開始値に
        if self.trend_type == 'return':
            pass
            #prices *= self.start_price / prices[-1]
        else:
            pass
            #prices *= self.end_price / prices[-1]

        today_str = date.today().strftime('%Y-%m-%d')
        print(today_str)
        dates = pd.bdate_range(start=today_str, periods=self.days)
        self.df = pd.DataFrame({'Date': dates, 'Price': prices})
        return self.df

    def _generate_trend1(self):
        """トレンドの骨格を生成"""
        if self.trend_type == 'down':
            t = np.linspace(0, 1, self.days)
            return self.start_price * (self.end_price / self.start_price) ** t
        
        elif self.trend_type == 'up':
            t = np.linspace(0, 1, self.days)
            return self.start_price * (self.end_price / self.start_price) ** t

        elif self.trend_type == 'v':
            half = self.days // 2
            down = np.linspace(0, 1, half)
            up = np.linspace(0, 1, self.days - half)
            decline = self.start_price * (self.min_price / self.start_price) ** down
            recovery = self.min_price * (self.end_price / self.min_price) ** up
            return np.concatenate([decline, recovery])

        elif self.trend_type == 'inverse_v':
            half = self.days // 2
            up = np.linspace(0, 1, half)
            down = np.linspace(0, 1, self.days - half)
            rise = self.start_price * (self.max_price / self.start_price) ** up
            fall = self.max_price * (self.end_price / self.max_price) ** down
            return np.concatenate([rise, fall])

        elif self.trend_type == 'return':
            # フラットに見せつつ、GBMノイズを乗せて最後に戻す
            return np.ones(self.days) * self.start_price

        elif self.trend_type == 'custom' and callable(self.custom_trend_func):
            return self.custom_trend_func(self.days, self.start_price, self.end_price)

        else:
            raise ValueError("Invalid trend_type or custom_trend_func not callable.")

    def _generate_trend(self):
        """生成されるトレンドの骨格（ノイズなし）"""
        if self.trend_type in ['up', 'down']:
            t = np.linspace(0, 1, self.days)
            trend = self.start_price * (self.end_price / self.start_price) ** t

        elif self.trend_type == 'v':
            half = self.days // 2
            down = np.linspace(0, 1, half)
            up = np.linspace(0, 1, self.days - half)
            decline = self.start_price * (self.min_price / self.start_price) ** down
            recovery = self.min_price * (self.end_price / self.min_price) ** up
            trend = np.concatenate([decline, recovery])

        elif self.trend_type == 'inverse_v':
            half = self.days // 2
            up = np.linspace(0, 1, half)
            down = np.linspace(0, 1, self.days - half)
            rise = self.start_price * (self.max_price / self.start_price) ** up
            fall = self.max_price * (self.end_price / self.max_price) ** down
            trend = np.concatenate([rise, fall])

        elif self.trend_type == 'return':
            # フラットに見せつつ、GBMノイズを乗せて最後に戻す
            trend = np.ones(self.days) * self.start_price

        elif self.trend_type == 'custom' and callable(self.custom_trend_func):
            trend = self.custom_trend_func(self.days, self.start_price, self.end_price)
        else:
            raise ValueError("Invalid trend_type or custom_trend_func not callable.")

        return trend

    def _generate_gbm_noise11(self):
        np.random.seed(self.random_seed)
        mu = np.log(self.end_price / self.start_price) / self.days
        epsilon = np.random.normal(0, 1, self.days)
        dt = 1 / 252
        returns = (mu - 0.5 * self.sigma**2) * dt + self.sigma * epsilon * np.sqrt(dt)

        for day, drop_ratio in self.crash_events:
            if 0 <= day < self.days:
                returns[day] += np.log(drop_ratio)  # e.g. np.log(0.9) ≒ -0.1053

        return returns

    def _generate_gbm_noise1(self):
        np.random.seed(self.random_seed)
        epsilon = np.random.normal(0, 1, self.days)
        mu = np.log(self.end_price / self.start_price) / self.days
        # epsilon = np.random.normal(loc=mu, scale=self.sigma, size=self.days)
        epsilon = np.random.normal(0, 1, self.days)
        dt = 1 / 252
        gbm_factors = np.exp((self.mu - 0.5 * self.sigma**2) * dt + self.sigma * epsilon * np.sqrt(dt))
        return np.cumprod(gbm_factors)

    def _generate_gbm_noise2(self):
        np.random.seed(self.random_seed)
        epsilon = np.random.normal(0, 1, self.days)
        gbm_factors = np.exp((self.mu - 0.5 * self.sigma**2) + self.sigma * epsilon)
        return np.cumprod(gbm_factors)

    def _set_crash_days(self, prices):
        crash_days = []
        for num in [0.2, 0.5, 0.8]:
            crash_days.append(int(self.days * 0.2))

        for day in crash_days:
            prices[day] = -0.15  # -15%の暴落
        
        stagnation_periods = []
        for num in [0.3, 0.7]:
            range1 = range(int(self.days * 0.3), int(self.days * 0.3) + 10)
            stagnation_periods.append(range1)

        for period in stagnation_periods:
            prices[list(period)] = np.random.normal(loc=0.0, scale=self.sigma * 0.3, size=len(period))

        # 株価生成（累積リターン）
        rprice = self.start_price * np.cumprod(1 + prices)
        return rprice

    def generate(self):

        # トレンドとノイズの合成
        base_trend = self._generate_trend()
        log_returns = self._generate_gbm_noise11()

        # 累積リターンを指数化して価格比に変換
        noise_factor = np.exp(np.cumsum(log_returns))

        # 最終価格系列
        prices = base_trend * noise_factor
        """
        base_trend = self._generate_trend()
        # noise = self._generate_gbm_noise11()
        base_trend = self._generate_gbm_noise11()
        # prices = base_trend * noise
        prices = self._set_crash_days(base_trend)
        # prices = base_trend
        """

        # 最終価格を狙ったend_priceに近づける
        # prices *= self.end_price / prices[-1]

        # 安全に範囲制限
        # prices = np.clip(prices, self.min_price, self.max_price)

        today_str = date.today().strftime('%Y-%m-%d')
        print(today_str)
        dates = pd.bdate_range(start=today_str, periods=self.days)
        self.df = pd.DataFrame({'Date': dates, 'Price': prices})
        return self.df

    def plot(self, title="Simulated Price Trend"):
        if self.df is None:
            self.generate()
        plt.figure(figsize=(14, 6))
        plt.plot(self.df['Date'], self.df['Price'], color='navy')

        print(self.df['Date'])

        # イベント描画
        for day, _ in self.crash_events:
            # plt.axvline(self.df['Date'][day], color='red', linestyle='--', alpha=0.5, label='Crash' if day == self.crash_events[0][0] else "")
            plt.axvline(self.df['Date'].iloc[day], color='red', linestyle='--', alpha=0.5, label='Crash' if day == self.crash_events[0][0] else "")

        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def save_csv(self, filename='simulated_price.csv'):
        if self.df is None:
            self.generate()
        print(f"saving {filename}")
        self.df.to_csv(filename, index=False)

if __name__ == "__main__":
    # 例：下がって上がって同じ価格で終わる（V字回復）
    
    idx1 = 'sp500'
    trend_type = 'inverse_v'
    sim = SimulatedMarket(
        start_price=6200,
        end_price=4500,
        min_price=4000,
        jump_day=1500,
        years=16,
        trend_type=trend_type
    )
    #  trend_type1 = "same"
    # df = sim.generate_with_jump()
    df = sim.generate()
    sim.plot("V-Recovery Simulation")
    sim.save_csv(f"{idx1}_{trend_type}.csv")