import pandas as pd
import numpy as np

def moving_avg_signal(df,window_short,window_long,col_name_override=None,save_in_df=True):

    return_df = None

    if 'asset_price_close' in df.columns:
        # Calculate moving averages based on windows defined earlier
        df['ma_short'] = df['asset_price_close'].rolling(window=window_short, min_periods=1, center=False).mean()
        df['ma_long'] = df['asset_price_close'].rolling(window=window_long, min_periods=1, center=False).mean()

        # Create signals: 1 if bullish, 0 if bearish
        df['signal'] = 0.0  # Preload with zeroes
        df['signal'].iloc[window_short:] = np.where(df['ma_short'][window_short:] > df['ma_long'][window_short:], 1.0, 0.0)  # Only for the period greater than the short MA -- IS THAT CORRECT? SHOULDN'T IT BE THE LONG MA?

        col_name = 'TRIGGER_' + str(window_short) + '_' + str(window_long) if col_name_override is None else col_name_override

        if save_in_df:
            # Generate triggers if the signal changed in the previous period: go long if 1, go short if -1
            df[col_name] = 0.0  # Preload with zeroes
            df[col_name] = df['signal'].diff().shift(1)
        else:
            return_df = df['signal'].diff().shift(1).copy(deep=True)

        return return_df
