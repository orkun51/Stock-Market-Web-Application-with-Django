from django.shortcuts import render, redirect
from .models import Stock
from .forms import StockForm
from django.contrib import messages
import requests
import json
import plotly.graph_objs as go
from .utils import get_plot


def get_plot(api):
    if api == "Error...":
        return None
    dates = [api['latestTime']]  # Adjust according to the actual API response format
    prices = [api['latestPrice']]  # Adjust according to the actual API response format
    plot = go.Figure(data=[go.Scatter(x=dates, y=prices, mode='lines+markers')])
    plot.update_layout(title='Stock Price Data', xaxis_title='Date', yaxis_title='Price')
    return plot.to_html(full_html=False)


# Home view to fetch and display single stock data
def home(request):
    import requests
    import json
    from .utils import get_plot  # Make sure this is correctly imported

    if request.method == 'POST':
        ticker = request.POST.get('ticker')
        api_key = "<Write your api key"
        api_request = requests.get(f"https://cloud.iexapis.com/stable/stock/{ticker}/chart/{api_key}")
        try:
            api = json.loads(api_request.content)
            # Prepare data for plotting
            dates = [data['date'] for data in api]
            prices = [float(data['close']) for data in api if 'close' in data]
            plot = get_plot(dates, prices)
        except Exception as e:
            api = "Error..."
            plot = None

        return render(request, 'home.html', {'api': api, 'plot': plot, 'ticker': ticker})
    else:
        return render(request, 'home.html', {'ticker': "Enter a Ticker Symbol Above"})



# About page view
def about(request):
    return render(request, 'about.html', {})

# View to add stocks to a user's watchlist
def add_stock(request):
    if request.method == 'POST':
        form = StockForm(request.POST or None)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Stock Has Been Added")
            return redirect('add_stock')
    else:
        ticker = Stock.objects.all()
        output = []
        for ticker_item in ticker:
            api_request = requests.get("https://cloud.iexapis.com/stable/stock/" + str(ticker_item) + "/quote?token=pk_67dc4aab3c8d45078b82ae83d8c810b0")
            try:
                api = json.loads(api_request.content)
                output.append(api)
            except Exception as e:
                api = "Error..."

        return render(request, 'add_stock.html', {'ticker': ticker, 'output': output})

# View to delete stocks from a user's watchlist
def delete(request, stock_id):
    item = Stock.objects.get(pk=stock_id)
    item.delete()
    messages.success(request, "Stock Has Been Deleted!")
    return redirect('delete_stock')

# Page to manage stock deletions
def delete_stock(request):
    ticker = Stock.objects.all()
    return render(request, 'delete_stock.html', {'ticker': ticker})


def stock_graph_view(request):
    # Default ticker symbol or fetch from GET request
    ticker = request.GET.get('ticker', 'AAPL')  # Default to 'AAPL' if no ticker is provided
    
    # Get the x_axis parameter from the URL or set a default value
    x_axis = request.GET.get('x_axis', 'Date')  # Default to 'Date' if not provided
    
    api_url = f"https://cloud.iexapis.com/stable/stock/{ticker}/quote?token=pk_67dc4aab3c8d45078b82ae83d8c810b0"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        api = response.json()
    except requests.RequestException as e:
        return render(request, 'error.html', {'error': str(e)})

    if 'latestTime' not in api or 'latestPrice' not in api:
        return render(request, 'error.html', {'error': 'Required data missing in API response'})

    dates = [api['latestTime']]
    prices = [api['latestPrice']]

    plot = go.Figure(data=[go.Scatter(x=dates, y=prices, mode='lines+markers')])
    plot.update_layout(title=f'Stock Price Data for {ticker}', xaxis_title=x_axis, yaxis_title='Price')
    plot_html = plot.to_html(full_html=False)

    return render(request, 'graphs.html', {'plot': plot_html, 'ticker': ticker, 'x_axis': x_axis})

