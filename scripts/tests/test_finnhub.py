from modules.finnhub import get_quote, search_symbol, get_stock_candles
print('Testing get_quote AAPL:')
try:
    print(get_quote('AAPL'))
except Exception as e:
    print(f'Error: {e}')
print('Testing search_symbol AAPL:')
try:
    print(search_symbol('AAPL'))
except Exception as e:
    print(f'Error: {e}')
print('Testing get_stock_candles AAPL recent:')
try:
    print(get_stock_candles('AAPL', '2024-03-01', '2024-03-07'))
except Exception as e:
    print(f'Error: {e}')
