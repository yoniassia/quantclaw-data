from modules.global_trade_helpdesk_api import list_countries, search_products, get_module_info
print('Testing list_countries:')
try:
    print(list_countries())
except Exception as e:
    print(f'Error: {e}')
print('Testing search_products electronics:')
try:
    print(search_products('electronics'))
except Exception as e:
    print(f'Error: {e}')
print('Testing get_module_info:')
try:
    print(get_module_info())
except Exception as e:
    print(f'Error: {e}')
