import requests

try:
    response = requests.get('https://dolarapi.com/v1/dolares', timeout=10)
    response.raise_for_status()
    data = response.json()
    print("API Response:")
    for rate in data:
        print(rate)
        if rate.get('casa') == 'blue':
            compra = rate.get('compra')
            print(f"Blue compra: {compra}, type: {type(compra)}")
except Exception as e:
    print(f"Error: {e}")