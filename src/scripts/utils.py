import numpy as np
import base64
import streamlit as st

from streamlit.components.v1 import html
def open_page(url):
    open_script= """
        <script type="text/javascript">
            window.open('%s', '_blank').focus();
        </script>
    """ % (url)
    html(open_script)

def hour_to_month(hourly_array):
    monthly_array = []
    summert = 0
    for i in range(0, len(hourly_array)):
        verdi = hourly_array[i]
        if np.isnan(verdi):
            verdi = 0
        summert = verdi + summert
        if i == 744 or i == 1416 or i == 2160 or i == 2880 \
                or i == 3624 or i == 4344 or i == 5088 or i == 5832 \
                or i == 6552 or i == 7296 or i == 8016 or i == 8759:
            monthly_array.append(int(summert))
            summert = 0
    return monthly_array 

def month_to_hour(monthly_array):
    hourly_array = np.zeros(8760)
    n, m = 0, 744
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 744, 1416
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 1416, 2160
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 2160, 2880
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 2880, 3624
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 3624, 4344
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 4344, 5088
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 5088, 5832
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 5832, 6552
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 6552, 7296
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 7296, 8016
    hourly_array[n:m] = monthly_array[0]/(m-n)
    n, m = 8016, 8760
    hourly_array[n:m] = monthly_array[0]/(m-n)
    #--
    return hourly_array
    

def render_svg(svg, text, result):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = f'<medium> {text} </medium> <br> <img src="data:image/svg+xml;base64,%s"/> <font size="+5">  {result} </font>' % b64
    st.write(html, unsafe_allow_html=True)